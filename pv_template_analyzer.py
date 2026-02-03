"""
Portable View Template Analyzer
AI-powered analysis of example documents to create reusable templates.
Uses vision models to understand document layout and structure.
"""

import os
import io
import json
import base64
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass

from pv_template_schema import (
    PortableTemplate, Section, SectionType, FieldMapping, FieldFormat,
    HeaderSection, DetailSection, TableSection, TextSection, ChartSection,
    ColumnDef, Alignment, PageLayout, Orientation, StyleConfig
)

log = logging.getLogger("pv_template_analyzer")

# Anthropic client (Claude on Azure) - lazy initialization
from report_genius.llm import create_azure_anthropic_client

_anthropic_client = None

def get_anthropic_client():
    """Lazily initialize the Anthropic client."""
    global _anthropic_client
    if _anthropic_client is None:
        _anthropic_client = create_azure_anthropic_client()
    return _anthropic_client

VISION_MODEL = os.environ.get("AZURE_DEPLOYMENT", "claude-sonnet-4-5")


@dataclass
class AnalysisResult:
    """Result of document analysis."""
    success: bool
    template: Optional[PortableTemplate] = None
    layout_description: str = ""
    identified_sections: List[Dict[str, Any]] = None
    field_mappings: List[Dict[str, Any]] = None
    suggestions: List[str] = None
    error: Optional[str] = None


ANALYSIS_SYSTEM_PROMPT = """You are an expert document analyst specializing in construction project management reports.
Your task is to analyze document images/descriptions and extract the structural layout for creating report templates.

When analyzing a document, identify:
1. **Layout**: Portrait/Landscape, margins, column structure
2. **Sections**: Headers, detail blocks, tables, charts, images, text areas
3. **Fields**: Data placeholders with their labels and likely data types
4. **Styling**: Colors, fonts, borders, spacing patterns

Output your analysis as structured JSON that can be used to create a template.

For field paths, use dot notation for nested properties:
- Simple: "Number", "Description", "Status"  
- Nested: "ContractorCompany.ShortLabel", "Status.Name"
- Child collections: "Items" (for tables)

Common Kahua field patterns:
- Numbers/IDs: "Number", "Id"
- Dates: "Date", "CreatedDateTime", "ScheduleStart", "ScheduleEnd"
- Status: "Status.Name"
- Companies: "ContractorCompany.ShortLabel", "ClientCompany.ShortLabel"
- Contacts: "Author.ShortLabel", "AssignedTo.ShortLabel"
- Currency: "TotalValue", "Amount", "OriginalContractAmount"
- Project: "DomainPartition.Name", "DomainPartition.Number"
"""

ANALYSIS_USER_PROMPT = """Analyze this document and extract its structure for creating a report template.

Target Entity: {entity_def}
User Guidance: {user_guidance}

Available fields from schema:
{available_fields}

Provide your analysis as JSON with this structure:
{{
  "layout": {{
    "orientation": "portrait" or "landscape",
    "estimated_margins": "normal" or "narrow" or "wide"
  }},
  "sections": [
    {{
      "type": "header" | "detail" | "table" | "text" | "chart" | "image",
      "title": "section title if visible",
      "order": 0,
      "description": "what this section contains",
      "fields": [
        {{"label": "visible label", "path": "suggested_field_path", "format": "text|date|currency|number"}}
      ],
      "table_columns": [  // only for table sections
        {{"label": "column header", "path": "field_path", "alignment": "left|center|right"}}
      ]
    }}
  ],
  "style": {{
    "primary_color": "#hex",
    "has_alternating_rows": true/false,
    "font_style": "professional" | "modern" | "minimal"
  }},
  "suggestions": ["any recommendations for improving the template"]
}}
"""


async def analyze_document_image(
    image_data: bytes,
    target_entity_def: str,
    available_fields: List[Dict[str, str]],
    user_guidance: str = ""
) -> AnalysisResult:
    """
    Analyze a document image using vision model to extract template structure.
    
    Args:
        image_data: Raw image bytes (PNG, JPEG, etc.)
        target_entity_def: The Kahua entity this template is for
        available_fields: List of available field definitions from schema
        user_guidance: Optional user instructions about what they want
    
    Returns:
        AnalysisResult with extracted template or error
    """
    try:
        # Encode image for API
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        # Format available fields for prompt
        fields_text = "\n".join([
            f"- {f.get('path', f.get('name', 'unknown'))}: {f.get('type', 'text')} - {f.get('label', '')}"
            for f in available_fields[:50]  # Limit to avoid token overflow
        ])
        
        response = await get_anthropic_client().messages.create(
            model=VISION_MODEL,
            system=ANALYSIS_SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_base64
                            }
                        },
                        {
                            "type": "text",
                            "text": ANALYSIS_USER_PROMPT.format(
                                entity_def=target_entity_def,
                                user_guidance=user_guidance or "Create a professional report template",
                                available_fields=fields_text
                            )
                        }
                    ]
                }
            ],
            max_tokens=4000,
            temperature=0.3
        )
        
        # Parse response
        content = response.content[0].text
        
        # Extract JSON from response (handle markdown code blocks)
        json_str = content
        if "```json" in content:
            json_str = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            json_str = content.split("```")[1].split("```")[0]
        
        analysis = json.loads(json_str)
        
        # Convert analysis to template
        template = _analysis_to_template(analysis, target_entity_def, user_guidance)
        
        return AnalysisResult(
            success=True,
            template=template,
            layout_description=json.dumps(analysis.get("layout", {})),
            identified_sections=analysis.get("sections", []),
            field_mappings=[f for s in analysis.get("sections", []) for f in s.get("fields", [])],
            suggestions=analysis.get("suggestions", [])
        )
        
    except json.JSONDecodeError as e:
        log.error(f"Failed to parse analysis JSON: {e}")
        return AnalysisResult(
            success=False,
            error=f"Failed to parse analysis response: {e}"
        )
    except Exception as e:
        log.error(f"Document analysis failed: {e}")
        return AnalysisResult(
            success=False,
            error=str(e)
        )


async def analyze_document_description(
    description: str,
    target_entity_def: str,
    available_fields: List[Dict[str, str]],
    user_guidance: str = ""
) -> AnalysisResult:
    """
    Create a template from a natural language description.
    
    Args:
        description: User's description of desired template
        target_entity_def: The Kahua entity this template is for
        available_fields: List of available field definitions from schema
        user_guidance: Additional context
    
    Returns:
        AnalysisResult with generated template
    """
    try:
        fields_text = "\n".join([
            f"- {f.get('path', f.get('name', 'unknown'))}: {f.get('type', 'text')} - {f.get('label', '')}"
            for f in available_fields[:50]
        ])
        
        prompt = f"""Create a report template based on this description:

Description: {description}

Target Entity: {target_entity_def}
Additional Guidance: {user_guidance}

Available fields:
{fields_text}

Provide the template structure as JSON (same format as document analysis).
"""
        
        response = await get_anthropic_client().messages.create(
            model=VISION_MODEL,
            system=ANALYSIS_SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=4000,
            temperature=0.4
        )
        
        content = response.content[0].text
        json_str = content
        if "```json" in content:
            json_str = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            json_str = content.split("```")[1].split("```")[0]
        
        analysis = json.loads(json_str)
        template = _analysis_to_template(analysis, target_entity_def, description)
        
        return AnalysisResult(
            success=True,
            template=template,
            layout_description=json.dumps(analysis.get("layout", {})),
            identified_sections=analysis.get("sections", []),
            suggestions=analysis.get("suggestions", [])
        )
        
    except Exception as e:
        log.error(f"Description analysis failed: {e}")
        return AnalysisResult(success=False, error=str(e))


def _analysis_to_template(
    analysis: Dict[str, Any],
    target_entity_def: str,
    source_description: str
) -> PortableTemplate:
    """Convert analysis JSON to PortableTemplate object."""
    
    # Layout
    layout_info = analysis.get("layout", {})
    orientation = Orientation.LANDSCAPE if layout_info.get("orientation") == "landscape" else Orientation.PORTRAIT
    
    margins = 1.0
    if layout_info.get("estimated_margins") == "narrow":
        margins = 0.5
    elif layout_info.get("estimated_margins") == "wide":
        margins = 1.5
    
    layout = PageLayout(
        orientation=orientation,
        margin_top=margins,
        margin_bottom=margins,
        margin_left=margins,
        margin_right=margins
    )
    
    # Style
    style_info = analysis.get("style", {})
    style = StyleConfig(
        primary_color=style_info.get("primary_color", "#1a365d"),
        secondary_color=style_info.get("secondary_color", "#3182ce")
    )
    
    # Sections
    sections = []
    for idx, s in enumerate(analysis.get("sections", [])):
        section = _create_section_from_analysis(s, idx)
        if section:
            sections.append(section)
    
    # Build template
    template = PortableTemplate(
        name=f"Template from Analysis",
        description=source_description[:200] if source_description else "Generated template",
        target_entity_def=target_entity_def,
        layout=layout,
        style=style,
        sections=sections,
        source_type="analysis",
        source_reference=source_description[:100] if source_description else None
    )
    
    return template


def _create_section_from_analysis(section_data: Dict[str, Any], order: int) -> Optional[Section]:
    """Create a Section object from analysis data."""
    
    section_type_str = section_data.get("type", "text").lower()
    type_map = {
        "header": SectionType.HEADER,
        "detail": SectionType.DETAIL,
        "table": SectionType.TABLE,
        "text": SectionType.TEXT,
        "chart": SectionType.CHART,
        "image": SectionType.IMAGE,
    }
    section_type = type_map.get(section_type_str, SectionType.TEXT)
    
    title = section_data.get("title")
    fields_data = section_data.get("fields", [])
    
    # Convert fields to FieldMapping objects
    fields = []
    for f in fields_data:
        format_map = {
            "date": FieldFormat.DATE,
            "datetime": FieldFormat.DATETIME,
            "currency": FieldFormat.CURRENCY,
            "number": FieldFormat.NUMBER,
            "percent": FieldFormat.PERCENT,
        }
        fmt = format_map.get(f.get("format", "").lower(), FieldFormat.TEXT)
        fields.append(FieldMapping(
            path=f.get("path", ""),
            label=f.get("label"),
            format=fmt
        ))
    
    section = Section(
        type=section_type,
        title=title,
        order=order
    )
    
    if section_type == SectionType.HEADER:
        section.header_config = HeaderSection(
            fields=fields,
            layout="grid",
            columns=2
        )
    
    elif section_type == SectionType.DETAIL:
        section.detail_config = DetailSection(
            fields=fields,
            layout="grid",
            columns=2
        )
    
    elif section_type == SectionType.TABLE:
        columns_data = section_data.get("table_columns", [])
        columns = []
        for c in columns_data:
            align_map = {"left": Alignment.LEFT, "center": Alignment.CENTER, "right": Alignment.RIGHT}
            columns.append(ColumnDef(
                field=FieldMapping(path=c.get("path", ""), label=c.get("label")),
                alignment=align_map.get(c.get("alignment", "left"), Alignment.LEFT)
            ))
        
        source = section_data.get("source", "Items")
        section.table_config = TableSection(
            source=source,
            columns=columns if columns else [ColumnDef(field=FieldMapping(path="Number"))]
        )
    
    elif section_type == SectionType.TEXT:
        content = section_data.get("content", section_data.get("description", ""))
        # Convert field references to template syntax
        for f in fields:
            if f.path:
                content = content.replace(f.label or f.path, f"{{{f.path}}}")
        section.text_config = TextSection(content=content)
    
    elif section_type == SectionType.CHART:
        section.chart_config = ChartSection(
            chart_type=section_data.get("chart_type", "bar"),
            title=title or "Chart",
            data_source=section_data.get("data_source", ""),
            label_field=section_data.get("label_field", ""),
            value_field=section_data.get("value_field", "")
        )
    
    return section


async def refine_template(
    template: PortableTemplate,
    instruction: str,
    available_fields: List[Dict[str, str]] = None
) -> Tuple[PortableTemplate, List[str]]:
    """
    Refine an existing template based on natural language instruction.
    
    Args:
        template: Existing template to modify
        instruction: User's modification request
        available_fields: Optional list of available fields for context
    
    Returns:
        Tuple of (modified template, list of changes made)
    """
    try:
        log.info(f"Refining template: {template.name} with instruction: {instruction[:100]}...")
        
        fields_text = ""
        if available_fields:
            fields_text = "\n".join([
                f"- {f.get('path', f.get('name', 'unknown'))}: {f.get('type', 'text')} ({f.get('label', '')})"
                for f in available_fields[:30]
            ])
        
        # Get entity info for context
        entity_name = template.target_entity_def.split('.')[-1] if template.target_entity_def else "Record"
        
        prompt = f"""Modify this template based on the user's instruction.

Entity Type: {entity_name}
Current Template (JSON):
{template.to_json()}

Available Fields:
{fields_text if fields_text else "No specific schema provided - use common field names for " + entity_name}

User Instruction: {instruction}

IMPORTANT: 
- Preserve the exact template JSON structure
- Keep all required fields (id, name, target_entity_def, layout, style, sections)
- For RFIs use fields like: Number, Subject, Status.Name, Priority.Name, DateSubmitted, DateRequired, Question, Answer, SubmittedBy.Name, AssignedTo.Name
- For Contracts use fields like: Number, Name, Description, Status.Name, OriginalAmount, RevisedAmount, StartDate, EndDate, Vendor.Name

Return ONLY valid JSON in this exact format:
```json
{{
  "template": {{ ... complete modified template ... }},
  "changes": ["change 1", "change 2"]
}}
```
"""
        
        log.debug(f"Sending prompt to Anthropic ({VISION_MODEL})...")
        
        response = await get_anthropic_client().messages.create(
            model=VISION_MODEL,
            system="You are a template editor. Modify templates based on user instructions while preserving valid JSON structure. Always return complete, valid template JSON.",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=4000,
            temperature=0.3
        )
        
        content = response.content[0].text
        log.debug(f"Received response: {content[:500]}...")
        
        # Extract JSON from response
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        
        result = json.loads(content)
        modified_template = PortableTemplate.from_dict(result.get("template", template.to_dict()))
        changes = result.get("changes", ["Template modified"])
        
        log.info(f"Template refinement successful: {changes}")
        return modified_template, changes
        
    except json.JSONDecodeError as e:
        log.error(f"JSON parsing failed: {e}")
        return template, [f"AI response was not valid JSON - please try a simpler request"]
    except Exception as e:
        log.error(f"Template refinement failed: {e}", exc_info=True)
        return template, [f"Refinement failed: {str(e)}"]


# ============== Utility Functions ==============

def extract_image_from_pdf(pdf_bytes: bytes, page_num: int = 0) -> bytes:
    """Extract a page from PDF as image for analysis."""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        page = doc[page_num]
        pix = page.get_pixmap(dpi=150)
        return pix.tobytes("png")
    except ImportError:
        raise RuntimeError("PyMuPDF (fitz) required for PDF processing. Install with: pip install pymupdf")


def extract_image_from_docx(docx_bytes: bytes) -> bytes:
    """Render first page of Word doc as image for analysis."""
    # This is complex - for now, suggest users provide PDF or image
    raise NotImplementedError(
        "Direct DOCX analysis not yet supported. "
        "Please export to PDF or take a screenshot of the desired layout."
    )
