"""
Agent Tools Module

All LangChain @tool-decorated functions for the Kahua Construction Analyst agent.
Organized by category: Kahua API, Templates (SOTA), Legacy Templates, DOCX Injection.
"""

import os
import json
import logging
from typing import Any, Dict, List
from pathlib import Path

import httpx
from langchain_core.tools import tool

log = logging.getLogger(__name__)

# ============== Configuration ==============

QUERY_URL_TEMPLATE = "https://demo01service.kahua.com/v2/domains/Summit/projects/{project_id}/query?returnDefaultAttributes=true"
KAHUA_BASIC_AUTH = os.getenv("KAHUA_BASIC_AUTH")


def _auth_header_value() -> str:
    if not KAHUA_BASIC_AUTH:
        raise RuntimeError("KAHUA_BASIC_AUTH not set")
    return KAHUA_BASIC_AUTH if KAHUA_BASIC_AUTH.strip().lower().startswith("basic ") \
           else f"Basic {KAHUA_BASIC_AUTH}"


HEADERS_JSON = lambda: {"Content-Type": "application/json", "Authorization": _auth_header_value()}

INJECTION_CONFIDENCE_THRESHOLD = float(os.getenv("RG_INJECTION_CONFIDENCE_THRESHOLD", "0.7"))

# Entity aliases for friendly names
ENTITY_ALIASES: Dict[str, str] = {
    "project": "kahua_Project.Project",
    "projects": "kahua_Project.Project",
    "rfi": "kahua_AEC_RFI.RFI",
    "rfis": "kahua_AEC_RFI.RFI",
    "submittal": "kahua_AEC_Submittal.Submittal",
    "submittals": "kahua_AEC_Submittal.Submittal",
    "change order": "kahua_AEC_ChangeOrder.ChangeOrder",
    "change orders": "kahua_AEC_ChangeOrder.ChangeOrder",
    "punchlist": "kahua_AEC_PunchList.PunchListItem",
    "punch list": "kahua_AEC_PunchList.PunchListItem",
    "contract": "kahua_Contract.Contract",
    "contracts": "kahua_Contract.Contract",
    "invoice": "kahua_ContractInvoice.ContractInvoice",
    "invoices": "kahua_ContractInvoice.ContractInvoice",
    "daily report": "kahua_AEC_DailyReport.DailyReport",
    "meeting": "kahua_Meeting.Meeting",
}


def resolve_entity_def(name_or_def: str) -> str:
    """Resolve friendly entity name to full definition."""
    key = (name_or_def or "").strip().lower()
    return ENTITY_ALIASES.get(key, name_or_def)


def _low_confidence_labels(placeholders: List[dict]) -> List[str]:
    return [
        p.get("label", "")
        for p in placeholders
        if float(p.get("confidence", 1.0)) < INJECTION_CONFIDENCE_THRESHOLD
    ]


# ============== Kahua API Tools ==============

@tool
def find_project(search_term: str) -> dict:
    """
    Find a project by name or partial match. ALWAYS use this when a user mentions a project by name.
    
    Args:
        search_term: Project name or partial name to search for (case-insensitive)
    
    Returns:
        Dict with matching projects including their IDs, names, and key details.
    """
    query_url = QUERY_URL_TEMPLATE.format(project_id=0)
    qpayload = {"PropertyName": "Query", "EntityDef": "kahua_Project.Project"}
    
    with httpx.Client(timeout=20.0) as client:
        resp = client.post(query_url, headers=HEADERS_JSON(), json=qpayload)
        if resp.status_code >= 400:
            return {"status": "error", "message": "Failed to query projects"}
        body = resp.json()
    
    projects = []
    for key in ("entities", "results", "items"):
        if isinstance(body.get(key), list):
            projects = body[key]
            break
    for s in body.get("sets", []):
        if isinstance(s.get("entities"), list) and s["entities"]:
            projects = s["entities"]
            break
    
    search_lower = search_term.lower()
    matches = []
    for proj in projects:
        name = proj.get("Name", proj.get("name", ""))
        if search_lower in name.lower():
            matches.append({
                "id": proj.get("Id", proj.get("id", proj.get("ProjectId"))),
                "name": name,
                "status": proj.get("Status", proj.get("status", "")),
            })
    
    if not matches:
        return {
            "status": "no_match",
            "search_term": search_term,
            "all_projects": [{"id": p.get("Id", p.get("id")), "name": p.get("Name", p.get("name", ""))} for p in projects[:20]]
        }
    
    return {"status": "ok", "matches": matches, "best_match": matches[0] if len(matches) == 1 else None}


@tool
def count_entities(entity_def: str, project_id: int = 0, scope: str = "Any") -> dict:
    """
    FAST count of a single entity type.
    
    Args:
        entity_def: Entity type - alias ("project", "rfi", "contract") or full name.
        project_id: Project context. Use 0 for domain-wide (default).
        scope: "Any" for all records across projects (default).
    
    Returns:
        Dict with count and entity info.
    """
    ent = resolve_entity_def(entity_def)
    query_url = QUERY_URL_TEMPLATE.format(project_id=project_id)
    qpayload: Dict[str, Any] = {"PropertyName": "Query", "EntityDef": ent, "Take": "1"}
    if scope:
        qpayload["Partition"] = {"Scope": scope}
    
    with httpx.Client(timeout=15.0) as client:
        resp = client.post(query_url, headers=HEADERS_JSON(), json=qpayload)
        if resp.status_code >= 400:
            return {"status": "error", "message": f"Failed to query {ent}"}
        body = resp.json()
    
    count = body.get("count", 0)
    return {"status": "ok", "entity_def": ent, "count": count, "project_id": project_id}


@tool
def query_entities(
    entity_def: str, 
    project_id: int = 0, 
    limit: int = 50,
    conditions_json: str = None,
    sort_by: str = None,
    sort_direction: str = "Ascending",
    scope: str = "Any"
) -> dict:
    """
    Query entities with filtering and sorting.
    
    Args:
        entity_def: Entity type alias or full name.
        project_id: Project ID. Use 0 for domain queries.
        limit: Max results (default 50).
        conditions_json: JSON string for filtering. Example: '[{"path": "Status", "type": "EqualTo", "value": "Open"}]'
        sort_by: Field to sort by.
        sort_direction: "Ascending" or "Descending".
        scope: Query scope ("Any" for cross-project).
    
    Returns:
        Dict with entities list and count.
    """
    ent = resolve_entity_def(entity_def)
    query_url = QUERY_URL_TEMPLATE.format(project_id=project_id)
    
    qpayload: Dict[str, Any] = {"PropertyName": "Query", "EntityDef": ent, "Take": str(limit)}
    
    if scope:
        qpayload["Partition"] = {"Scope": scope}
    
    if conditions_json:
        try:
            conditions = json.loads(conditions_json)
            kahua_conditions = []
            for cond in conditions:
                kahua_conditions.append({
                    "PropertyName": "Data",
                    "Path": cond["path"],
                    "Type": cond["type"],
                    "Value": cond.get("value", "")
                })
            if kahua_conditions:
                qpayload["Condition"] = kahua_conditions
        except json.JSONDecodeError:
            pass
    
    if sort_by:
        qpayload["Sorts"] = [{"PropertyName": "Data", "Path": sort_by, "Direction": sort_direction}]
    
    with httpx.Client(timeout=30.0) as client:
        resp = client.post(query_url, headers=HEADERS_JSON(), json=qpayload)
        body = resp.json() if resp.status_code < 400 else {}
    
    entities = []
    count = body.get("count", 0)
    for k in ("entities", "results", "items"):
        if isinstance(body.get(k), list):
            entities = body[k]
            break
    for s in body.get("sets", []):
        if isinstance(s.get("entities"), list):
            entities = s["entities"]
            break
    
    return {"status": "ok", "entity_def": ent, "count": count, "returned": len(entities), "entities": entities}


@tool
def get_entity_schema(entity_def: str, project_id: int = 0) -> dict:
    """
    Get the field schema for an entity type by sampling a record.
    
    Args:
        entity_def: The entity type to inspect.
        project_id: Project context.
    
    Returns:
        Dict with field names and sample values.
    """
    ent = resolve_entity_def(entity_def)
    query_url = QUERY_URL_TEMPLATE.format(project_id=project_id)
    qpayload = {"PropertyName": "Query", "EntityDef": ent, "Take": "1", "Partition": {"Scope": "Any"}}
    
    with httpx.Client(timeout=15.0) as client:
        resp = client.post(query_url, headers=HEADERS_JSON(), json=qpayload)
        if resp.status_code >= 400:
            return {"status": "error", "message": f"Failed to query {ent}"}
        body = resp.json()
    
    sample = None
    for key in ("entities", "results", "items"):
        if isinstance(body.get(key), list) and body[key]:
            sample = body[key][0]
            break
    for s in body.get("sets", []):
        if isinstance(s.get("entities"), list) and s["entities"]:
            sample = s["entities"][0]
            break
    
    if not sample:
        return {"status": "ok", "entity_def": ent, "fields": [], "message": "No records found"}
    
    fields = [{"name": k, "type": type(v).__name__, "sample": str(v)[:100]} for k, v in sample.items()]
    return {"status": "ok", "entity_def": ent, "fields": sorted(fields, key=lambda x: x["name"])}


@tool
def generate_report(
    title: str,
    markdown_content: str,
    subtitle: str = None,
    charts_json: str = None
) -> dict:
    """
    Generate an ANALYTICS REPORT document from markdown and charts.
    
    THIS IS NOT FOR TEMPLATES!
    For templates/portable views, use build_custom_template instead.
    
    This tool creates ONE-TIME REPORTS with:
    - Actual data values (not placeholders)
    - Dark blue header banner with the title
    - Charts and analysis
    
    For Kahua portable view templates (reusable templates with placeholders like
    [Attribute(Number)]), use `build_custom_template` + `render_smart_template` instead.
    
    Args:
        title: Report title (appears in dark blue banner).
        markdown_content: Body content with actual data values.
        subtitle: Optional subtitle.
        charts_json: JSON array of chart specs.
    
    Returns:
        Dict with filename and download URL.
    """
    try:
        from report_generator import create_report
        charts = json.loads(charts_json) if charts_json else None
        result = create_report(title=title, markdown_content=markdown_content, charts=charts, subtitle=subtitle)
        filename = result["filename"]
        base_url = os.getenv("REPORT_BASE_URL", "http://localhost:8000")
        return {"status": "ok", "filename": filename, "download_url": f"{base_url}/reports/{filename}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ============== Collect Kahua API tools ==============

KAHUA_API_TOOLS = [find_project, count_entities, query_entities, get_entity_schema, generate_report]


# ============== SOTA Template Tools ==============

# Storage for templates being built interactively
_active_templates: Dict[str, dict] = {}


def _get_unified_system():
    """Lazy import the unified template system."""
    from unified_templates import get_unified_system
    return get_unified_system()


@tool
def list_template_archetypes() -> dict:
    """
    List available template archetypes (design patterns).
    
    Each archetype is optimized for a specific document purpose:
    - formal_document: Contracts, agreements requiring signatures
    - executive_summary: Quick overview for leadership
    - financial_report: Cost breakdowns, line items, totals
    - correspondence: RFIs, submittals with Q&A pattern
    - field_report: Observations, inspections
    - checklist: Punch lists, inspection items
    
    Returns:
        Dict with list of archetypes and descriptions
    """
    system = _get_unified_system()
    return {"status": "ok", "archetypes": system.get_archetypes()}


@tool
def list_template_entities() -> dict:
    """
    List entity types available for SOTA template generation.
    
    These are pre-analyzed entity schemas with intelligent field categorization.
    
    Returns:
        Dict with list of entities and their field counts
    """
    system = _get_unified_system()
    entities = []
    for name, schema in system.tg_schemas.items():
        entities.append({
            "id": name,
            "name": schema.name,
            "entity_def": schema.entity_def,
            "field_count": len(schema.fields),
        })
    return {"status": "ok", "entities": entities}


@tool
def smart_compose_template(
    entity_type: str,
    archetype: str = None,
    user_intent: str = None,
    name: str = None
) -> dict:
    """
    Create a professional template using SOTA AI-powered composition.
    
    This tool uses intelligent design patterns to create well-structured
    templates with proper visual hierarchy, field grouping, and Kahua syntax.
    
    Args:
        entity_type: Entity type (e.g., "Invoice", "RFI", "ExpenseContract")
        archetype: Optional design pattern ("financial_report", "correspondence", etc.)
                  Auto-inferred if not provided.
        user_intent: Natural language description (e.g., "executive summary for board")
        name: Custom template name
    
    Returns:
        Dict with template structure and sections summary
    """
    try:
        from report_genius.config import TEMPLATES_DIR
        
        system = _get_unified_system()
        template = system.compose_smart(
            entity_type=entity_type,
            archetype=archetype,
            user_intent=user_intent,
            name=name,
        )
        
        # Save to disk
        TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
        json_path = TEMPLATES_DIR / f"{template.id}.json"
        json_path.write_text(template.model_dump_json(indent=2))
        
        # Build summary
        sections_summary = []
        for s in template.get_sections_ordered():
            config = s.get_config()
            field_count = 0
            if hasattr(config, 'fields'):
                field_count = len(config.fields)
            elif hasattr(config, 'columns'):
                field_count = len(config.columns)
            sections_summary.append({
                "type": s.type.value,
                "title": s.title or "(header)",
                "field_count": field_count,
            })
        
        return {
            "status": "ok",
            "template_id": template.id,
            "name": template.name,
            "entity_def": template.entity_def,
            "archetype": archetype or "auto-inferred",
            "sections": sections_summary,
            "saved_to": str(json_path),
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@tool
def render_smart_template(template_id: str, output_name: str = None) -> dict:
    """
    Render a SOTA template to Word document with Kahua placeholder syntax.
    
    The generated DOCX contains proper Kahua placeholders like:
    - [Attribute(Path)] for text fields
    - [Currency(Source=Attribute,Path=...,Format="C2")] for money
    - [Date(Source=Attribute,Path=...,Format="d")] for dates
    - [StartTable(...)] / [EndTable] for collections
    
    This is ready to be uploaded to Kahua configuration.
    
    Args:
        template_id: Template ID from smart_compose_template
        output_name: Optional custom filename (without extension)
    
    Returns:
        Dict with download URL for the generated document
    """
    try:
        from report_genius.templates import PortableViewTemplate
        from report_genius.config import TEMPLATES_DIR, REPORTS_DIR
        
        # Find template
        json_path = TEMPLATES_DIR / f"{template_id}.json"
        
        if not json_path.exists():
            return {"status": "error", "message": f"Template {template_id} not found"}
        
        # Load and render
        template = PortableViewTemplate.model_validate_json(json_path.read_text())
        system = _get_unified_system()
        
        REPORTS_DIR.mkdir(exist_ok=True)
        
        filename = output_name or template_id
        docx_path = REPORTS_DIR / f"{filename}.docx"
        system.render_to_docx(template, docx_path)
        
        base_url = os.getenv("REPORT_BASE_URL", "http://localhost:8000")
        
        return {
            "status": "ok",
            "filename": docx_path.name,
            "download_url": f"{base_url}/reports/{docx_path.name}",
            "template_name": template.name,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@tool
def get_entity_fields(entity_type: str, category: str = None) -> dict:
    """
    Show all available fields for an entity type, organized by category.
    
    USE THIS FIRST when a user asks for a template - show them what fields
    are available so they can tell you what they want included.
    
    Args:
        entity_type: Entity type (e.g., "Invoice", "RFI", "ExpenseContract")
        category: Optional filter - "identity", "financial", "date", "contact", 
                 "text_block", "status", "collection", etc.
    
    Returns:
        Dict with fields organized by category, with labels and suggested formats
    """
    try:
        system = _get_unified_system()
        entity_key = None
        entity_lower = entity_type.lower()
        for key in system.tg_schemas:
            if key.lower() == entity_lower:
                entity_key = key
                break
        
        if not entity_key:
            return {"status": "error", "message": f"Unknown entity: {entity_type}", 
                   "available": list(system.tg_schemas.keys())}
        
        schema = system.tg_schemas[entity_key]
        
        # Organize fields by category
        fields_by_category = {}
        for field_info in schema.fields:
            cat = field_info.category.value
            if category and cat != category:
                continue
            if cat not in fields_by_category:
                fields_by_category[cat] = []
            fields_by_category[cat].append({
                "path": field_info.path,
                "label": field_info.label,
                "format": field_info.format_hint or "text",
                "is_optional": field_info.is_optional,
            })
        
        return {
            "status": "ok",
            "entity_type": entity_key,
            "entity_def": schema.entity_def,
            "fields_by_category": fields_by_category,
            "total_fields": len(schema.fields),
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@tool
def build_custom_template(
    entity_type: str,
    name: str,
    sections_json: str,
    include_logo: bool = True,
    layout: str = "single_column",
    static_title: str = None,
    title_style_json: str = None,
    page_header_json: str = None,
    page_footer_json: str = None
) -> dict:
    """
    Build a portable view template with Kahua placeholders.
    
    THIS CREATES AN ACTUAL TEMPLATE WITH PLACEHOLDERS - not a specification document.
    The output is a Word document ready to be used with Kahua data.
    
    Args:
        entity_type: Entity type (e.g., "Invoice", "RFI")
        name: Template name (for identification, not displayed in document)
        sections_json: JSON array of section specs. Each section:
            {
                "type": "header" | "detail" | "table" | "text" | "list",
                "title": "Section Title" (optional),
                "fields": ["FieldPath1", "FieldPath2", ...],
                "formatting": {
                    "bold_fields": ["FieldPath1"],
                    "columns": 2,
                },
                "list_type": "bullet" | "number",
                "items": ["Item 1", "Item 2 with {Field}"]
            }
        include_logo: Whether to include company logo placeholder
        layout: "single_column" or "two_column"
        static_title: A literal text title to display (e.g., "Beaus RFI Template")
        title_style_json: JSON object for title styling:
            {"font": "Comic Sans MS", "size": 28, "color": "#0000FF", "bold": true, "alignment": "center"}
        page_header_json: JSON object for page header config
        page_footer_json: JSON object for page footer config
    
    Returns:
        Dict with template_id and structure summary
    """
    try:
        import uuid
        from report_genius.templates import (
            PortableViewTemplate, Section, SectionType,
            HeaderConfig, DetailConfig, TableConfig, TextConfig, ListConfig,
            FieldDef, FieldFormat as TGFieldFormat, TableColumn,
            LayoutConfig, PageHeaderFooterConfig, Alignment,
        )
        from report_genius.config import TEMPLATES_DIR
        
        system = _get_unified_system()
        
        # Resolve entity
        entity_key = None
        entity_lower = entity_type.lower()
        for key in system.tg_schemas:
            if key.lower() == entity_lower:
                entity_key = key
                break
        
        if not entity_key:
            return {"status": "error", "message": f"Unknown entity: {entity_type}"}
        
        schema = system.tg_schemas[entity_key]
        
        # Parse sections
        sections_spec = json.loads(sections_json)
        
        # Build field lookup for format hints
        field_lookup = {f.path: f for f in schema.fields}
        field_lookup.update({f.path.lower(): f for f in schema.fields})
        field_lookup.update({f.label.lower(): f for f in schema.fields})
        
        def resolve_field(field_name: str) -> FieldDef:
            """Resolve a field name to FieldDef with proper formatting."""
            f = field_lookup.get(field_name) or field_lookup.get(field_name.lower())
            if f:
                fmt = TGFieldFormat.TEXT
                if f.category.value == "financial":
                    fmt = TGFieldFormat.CURRENCY
                elif f.category.value == "date":
                    fmt = TGFieldFormat.DATE
                elif f.category.value == "numeric":
                    fmt = TGFieldFormat.NUMBER
                return FieldDef(path=f.path, label=f.label, format=fmt)
            return FieldDef(path=field_name, label=field_name.replace("_", " ").title(), format=TGFieldFormat.TEXT)
        
        # Build sections
        built_sections = []
        has_header = any(spec.get("type") == "header" for spec in sections_spec)
        
        # Parse title style
        title_style = {}
        if title_style_json:
            try:
                title_style = json.loads(title_style_json)
            except:
                pass
        
        align_map = {"left": Alignment.LEFT, "center": Alignment.CENTER, "right": Alignment.RIGHT}
        title_alignment = align_map.get(title_style.get("alignment", "left"), Alignment.LEFT)
        
        # Auto-create header section if none specified and logo is requested
        if not has_header and include_logo:
            title_field_path = "Number"
            subtitle_field_path = "Subject"
            
            for f in schema.fields:
                if f.category.value == "identity":
                    if f.path.lower() in ["number", "id", "reference"]:
                        title_field_path = f.path
                    elif f.path.lower() in ["subject", "name", "title", "description"]:
                        subtitle_field_path = f.path
            
            auto_header = HeaderConfig(
                title_template=f"{{{title_field_path}}}",
                subtitle_template=f"{{{subtitle_field_path}}}",
                fields=[],
                show_logo=True,
                static_title=static_title,
                title_font=title_style.get("font"),
                title_size=title_style.get("size"),
                title_color=title_style.get("color"),
                title_bold=title_style.get("bold", True),
                title_alignment=title_alignment,
            )
            built_sections.append(Section(
                type=SectionType.HEADER, order=0, header_config=auto_header
            ))
        
        for idx, spec in enumerate(sections_spec):
            sec_type = SectionType(spec.get("type", "detail"))
            title = spec.get("title", "")
            fields = spec.get("fields", [])
            formatting = spec.get("formatting", {})
            section_order = idx + 1 if (not has_header and include_logo) else idx
            
            if sec_type == SectionType.HEADER:
                field_defs = [resolve_field(f) for f in fields]
                title_field = field_defs[0] if field_defs else None
                
                config = HeaderConfig(
                    title_template=f"{{{title_field.path}}}" if title_field else "{Number}",
                    subtitle_template=f"{{{field_defs[1].path}}}" if len(field_defs) > 1 else None,
                    fields=field_defs[2:] if len(field_defs) > 2 else [],
                    show_logo=include_logo,
                    static_title=static_title,
                    title_font=title_style.get("font"),
                    title_size=title_style.get("size"),
                    title_color=title_style.get("color"),
                    title_bold=title_style.get("bold", True),
                    title_alignment=title_alignment,
                )
                built_sections.append(Section(
                    type=SectionType.HEADER, order=section_order, header_config=config
                ))
                
            elif sec_type == SectionType.DETAIL:
                field_defs = [resolve_field(f) for f in fields]
                bold_fields = [bf.lower() for bf in formatting.get("bold_fields", [])]
                for fd in field_defs:
                    if fd.path.lower() in bold_fields or fd.label.lower() in bold_fields:
                        fd.emphasis = "bold"
                
                config = DetailConfig(
                    fields=field_defs,
                    columns=formatting.get("columns", 2),
                )
                built_sections.append(Section(
                    type=SectionType.DETAIL, title=title, order=section_order, detail_config=config
                ))
                
            elif sec_type == SectionType.TABLE:
                source = spec.get("source", fields[0] if fields else "Items")
                columns = [TableColumn(field=resolve_field(f)) for f in fields]
                config = TableConfig(source=source, columns=columns, show_header=True)
                built_sections.append(Section(
                    type=SectionType.TABLE, title=title, order=section_order, table_config=config
                ))
                
            elif sec_type == SectionType.TEXT:
                content = spec.get("content", "")
                if not content and fields:
                    content = "\n\n".join(f"{{{f}}}" for f in fields)
                config = TextConfig(content=content)
                built_sections.append(Section(
                    type=SectionType.TEXT, title=title, order=section_order, text_config=config
                ))
                
            elif sec_type == SectionType.LIST:
                list_type = spec.get("list_type", "bullet")
                items = spec.get("items", fields)
                config = ListConfig(list_type=list_type, items=items)
                built_sections.append(Section(
                    type=SectionType.LIST, title=title, order=section_order, list_config=config
                ))
        
        # Parse page header/footer configs
        page_header_config = None
        if page_header_json:
            try:
                ph_data = json.loads(page_header_json)
                page_header_config = PageHeaderFooterConfig(**ph_data)
            except:
                pass
        
        page_footer_config = None
        if page_footer_json:
            try:
                pf_data = json.loads(page_footer_json)
                page_footer_config = PageHeaderFooterConfig(**pf_data)
            except:
                pass
        
        # Create template
        template_id = f"pv-{uuid.uuid4().hex[:8]}"
        template = PortableViewTemplate(
            id=template_id,
            name=name,
            entity_def=schema.entity_def,
            version="1.0",
            sections=built_sections,
            layout=LayoutConfig(
                columns=2 if layout == "two_column" else 1,
                page_header=page_header_config,
                page_footer=page_footer_config,
            ),
        )
        
        # Save to disk
        TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
        json_path = TEMPLATES_DIR / f"{template_id}.json"
        json_path.write_text(template.model_dump_json(indent=2))
        
        _active_templates[template_id] = template.model_dump()
        
        # Build summary
        sections_summary = []
        for s in built_sections:
            cfg = s.get_config()
            field_count = 0
            field_names = []
            if hasattr(cfg, 'fields'):
                field_count = len(cfg.fields)
                field_names = [f.label for f in cfg.fields[:5]]
            elif hasattr(cfg, 'columns'):
                field_count = len(cfg.columns)
                field_names = [c.field.label for c in cfg.columns[:5]]
            sections_summary.append({
                "type": s.type.value,
                "title": s.title or "(no title)",
                "field_count": field_count,
                "fields": field_names,
            })
        
        return {
            "status": "ok",
            "template_id": template_id,
            "name": name,
            "entity_def": schema.entity_def,
            "sections": sections_summary,
            "include_logo": include_logo,
            "saved_to": str(json_path),
            "message": f"Template created. Call render_smart_template('{template_id}') to generate DOCX.",
        }
    except Exception as e:
        import traceback
        return {"status": "error", "message": str(e), "trace": traceback.format_exc()}


@tool
def modify_existing_template(
    template_id: str,
    operation: str,
    config_json: str = None
) -> dict:
    """
    Modify an existing template based on user feedback.
    
    Use this when user asks to change something about a template:
    - "remove the logo"
    - "make the subject bold"
    - "add the Due Date field"
    
    Args:
        template_id: The template to modify
        operation: One of:
            - "add_fields" - Add fields to a section
            - "remove_fields" - Remove fields from a section
            - "add_section" - Add a new section
            - "remove_section" - Remove a section
            - "toggle_logo" - Turn logo on/off
            - "set_bold" - Make specific fields bold
            - "set_columns" - Change column count in a section
        config_json: JSON config for the operation
    
    Returns:
        Dict with updated template structure
    """
    try:
        from report_genius.templates import (
            PortableViewTemplate, Section, SectionType,
            HeaderConfig, DetailConfig, FieldDef, FieldFormat as TGFieldFormat,
        )
        from report_genius.config import TEMPLATES_DIR
        
        json_path = TEMPLATES_DIR / f"{template_id}.json"
        
        if not json_path.exists():
            return {"status": "error", "message": f"Template {template_id} not found"}
        
        template = PortableViewTemplate.model_validate_json(json_path.read_text())
        config = json.loads(config_json) if config_json else {}
        
        if operation == "toggle_logo":
            for section in template.sections:
                if section.type == SectionType.HEADER and section.header_config:
                    section.header_config.show_logo = config.get("show", True)
                    
        elif operation == "add_fields":
            sec_idx = config.get("section_index", 0)
            new_fields = config.get("fields", [])
            if 0 <= sec_idx < len(template.sections):
                section = template.sections[sec_idx]
                if section.detail_config:
                    for f in new_fields:
                        section.detail_config.fields.append(
                            FieldDef(path=f, label=f.replace("_", " ").title())
                        )
                        
        elif operation == "remove_fields":
            sec_idx = config.get("section_index", 0)
            remove_fields = [f.lower() for f in config.get("fields", [])]
            if 0 <= sec_idx < len(template.sections):
                section = template.sections[sec_idx]
                if section.detail_config:
                    section.detail_config.fields = [
                        f for f in section.detail_config.fields
                        if f.path.lower() not in remove_fields and f.label.lower() not in remove_fields
                    ]
                    
        elif operation == "remove_section":
            sec_idx = config.get("section_index", 0)
            if 0 <= sec_idx < len(template.sections):
                template.sections.pop(sec_idx)
                for i, s in enumerate(template.sections):
                    s.order = i
                    
        elif operation == "set_bold":
            bold_fields = [f.lower() for f in config.get("fields", [])]
            for section in template.sections:
                if section.detail_config:
                    for field in section.detail_config.fields:
                        if field.path.lower() in bold_fields or field.label.lower() in bold_fields:
                            field.emphasis = "bold"
                            
        elif operation == "set_columns":
            sec_idx = config.get("section_index", 0)
            columns = config.get("columns", 2)
            if 0 <= sec_idx < len(template.sections):
                section = template.sections[sec_idx]
                if section.detail_config:
                    section.detail_config.columns = columns
        
        # Save updated template
        json_path.write_text(template.model_dump_json(indent=2))
        _active_templates[template_id] = template.model_dump()
        
        # Build summary
        sections_summary = []
        for s in template.sections:
            cfg = s.get_config()
            field_names = []
            if hasattr(cfg, 'fields'):
                field_names = [f.label for f in cfg.fields[:5]]
            elif hasattr(cfg, 'columns'):
                field_names = [c.field.label for c in cfg.columns[:5]]
            sections_summary.append({
                "type": s.type.value,
                "title": s.title or "(header)",
                "fields": field_names,
            })
        
        return {
            "status": "ok",
            "template_id": template_id,
            "operation": operation,
            "sections": sections_summary,
            "message": f"Template updated. Call render_smart_template('{template_id}') to generate DOCX.",
        }
    except Exception as e:
        import traceback
        return {"status": "error", "message": str(e), "trace": traceback.format_exc()}


@tool  
def preview_template_structure(template_id: str) -> dict:
    """
    Show the current structure of a template so user can see what will be generated.
    
    Args:
        template_id: Template to preview
        
    Returns:
        Dict with detailed template structure including all sections and fields
    """
    try:
        from report_genius.templates import PortableViewTemplate
        from report_genius.config import TEMPLATES_DIR
        
        json_path = TEMPLATES_DIR / f"{template_id}.json"
        
        if not json_path.exists():
            return {"status": "error", "message": f"Template {template_id} not found"}
        
        template = PortableViewTemplate.model_validate_json(json_path.read_text())
        
        sections_detail = []
        for s in template.sections:
            cfg = s.get_config()
            detail = {
                "type": s.type.value,
                "title": s.title or "(header)",
                "order": s.order,
            }
            
            if hasattr(cfg, 'show_logo'):
                detail["show_logo"] = cfg.show_logo
            if hasattr(cfg, 'fields'):
                detail["fields"] = [
                    {"path": f.path, "label": f.label, "format": f.format.value if f.format else "text", 
                     "bold": getattr(f, 'emphasis', None) == 'bold'}
                    for f in cfg.fields
                ]
            if hasattr(cfg, 'columns') and isinstance(cfg.columns, int):
                detail["column_layout"] = cfg.columns
            if hasattr(cfg, 'columns') and isinstance(cfg.columns, list):
                detail["table_columns"] = [
                    {"path": c.field.path, "label": c.field.label}
                    for c in cfg.columns
                ]
                
            sections_detail.append(detail)
        
        return {
            "status": "ok",
            "template_id": template_id,
            "name": template.name,
            "entity_def": template.entity_def,
            "sections": sections_detail,
            "layout_columns": template.layout.columns if template.layout else 1,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ============== Collect SOTA Template tools ==============

SOTA_TEMPLATE_TOOLS = [
    list_template_archetypes,
    list_template_entities,
    smart_compose_template,
    render_smart_template,
    get_entity_fields,
    build_custom_template,
    modify_existing_template,
    preview_template_structure,
]


# ============== DOCX Token Injection Tools ==============

def _get_uploads_dir() -> Path:
    """Get uploads directory."""
    uploads = Path(__file__).parent.parent.parent.parent / "uploads"
    uploads.mkdir(exist_ok=True)
    return uploads


@tool
def analyze_uploaded_template(filename: str, entity_def: str = "") -> dict:
    """
    Analyze an uploaded DOCX template and detect placeholder patterns.
    
    This tool examines a Word document that may have "blank" template patterns like:
    - "ID: " (label with trailing whitespace)
    - "Status: ______" (label with underscores)
    
    Args:
        filename: The uploaded file name (in uploads/ directory)
        entity_def: Target Kahua entity (e.g., "kahua_AEC_RFI.RFI") for better field mapping
        
    Returns:
        Dict with detected placeholders and suggestions
    """
    try:
        from report_genius.injection import analyze_and_inject
        
        file_path = _get_uploads_dir() / filename
        if not file_path.exists():
            return {"status": "error", "message": f"File not found: {filename}"}
        
        if not filename.lower().endswith(('.docx', '.doc')):
            return {"status": "error", "message": "Only Word documents (.docx) are supported"}
        
        doc_bytes = file_path.read_bytes()
        result = analyze_and_inject(doc_bytes, entity_def=entity_def, auto_inject=False)
        
        return {
            "status": "ok",
            "filename": filename,
            "entity_def": entity_def or "(not specified)",
            "analysis": result['analysis']
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@tool
def inject_tokens_into_template(
    filename: str,
    entity_def: str = "",
    add_logo: bool = True,
    add_timestamp: bool = True,
    allow_low_confidence: bool = False,
) -> dict:
    """
    Inject Kahua tokens into an uploaded template based on detected patterns.
    
    Should be called AFTER analyze_uploaded_template.
    
    Args:
        filename: The uploaded file name to modify
        entity_def: Target Kahua entity for better field mapping
        add_logo: Add [CompanyLogo(...)] placeholder to header
        add_timestamp: Add [ReportModifiedTimeStamp] to footer
        allow_low_confidence: Proceed even if low-confidence mappings are detected
        
    Returns:
        Dict with modified filename and download URL
    """
    try:
        from report_genius.injection import analyze_and_inject, add_logo_placeholder, add_timestamp_token
        
        file_path = _get_uploads_dir() / filename
        if not file_path.exists():
            return {"status": "error", "message": f"File not found: {filename}"}
        
        doc_bytes = file_path.read_bytes()
        analysis = analyze_and_inject(doc_bytes, entity_def=entity_def, auto_inject=False)
        low_confidence = _low_confidence_labels(analysis["analysis"]["placeholders"])
        if low_confidence and not allow_low_confidence:
            return {
                "status": "needs_confirmation",
                "message": "Low-confidence mappings detected. Confirm to proceed.",
                "low_confidence": low_confidence,
                "analysis": analysis["analysis"],
            }

        result = analyze_and_inject(doc_bytes, entity_def=entity_def, auto_inject=True)
        
        if not result.get('injection', {}).get('success'):
            return {
                "status": "error", 
                "message": result.get('injection', {}).get('error', 'Injection failed')
            }
        
        modified_doc = result.get('modified_document', doc_bytes)
        aesthetics_added = []
        
        if add_logo:
            modified_doc = add_logo_placeholder(modified_doc, position='header')
            aesthetics_added.append("company_logo")
        
        if add_timestamp:
            modified_doc = add_timestamp_token(modified_doc, position='footer')
            aesthetics_added.append("timestamp")
        
        # Save modified document
        modified_filename = f"tokenized_{filename}"
        modified_path = _get_uploads_dir() / modified_filename
        modified_path.write_bytes(modified_doc)
        
        # Also copy to reports for download
        from report_genius.config import REPORTS_DIR
        REPORTS_DIR.mkdir(exist_ok=True)
        (REPORTS_DIR / modified_filename).write_bytes(modified_doc)
        
        base_url = os.getenv("REPORT_BASE_URL", "http://localhost:8000")
        
        return {
            "status": "ok",
            "original_filename": filename,
            "modified_filename": modified_filename,
            "download_url": f"{base_url}/reports/{modified_filename}",
            "tokens_injected": result['injection']['tokens_injected'],
            "changes": result['injection']['changes_made'],
            "aesthetics_added": aesthetics_added,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@tool
def show_token_mapping_guide() -> dict:
    """
    Show the label-to-token mapping guide.
    
    Returns the mapping rules used to convert labels like "ID:" to Kahua paths.
    
    Returns:
        Dict with common label mappings organized by category
    """
    try:
        from report_genius.injection import LABEL_NORMALIZATIONS
        
        identity = {}
        dates = {}
        contacts = {}
        financial = {}
        text = {}
        status = {}
        other = {}
        
        for label, path in LABEL_NORMALIZATIONS.items():
            if any(x in label for x in ['id', 'number', 'name', 'subject', 'title', 'ref']):
                identity[label] = path
            elif any(x in label for x in ['date', 'due', 'start', 'end', 'created', 'modified']):
                dates[label] = path
            elif any(x in label for x in ['from', 'to', 'by', 'author', 'contact', 'company']):
                contacts[label] = path
            elif any(x in label for x in ['amount', 'cost', 'price', 'total', 'value']):
                financial[label] = path
            elif any(x in label for x in ['description', 'notes', 'scope', 'question', 'answer']):
                text[label] = path
            elif any(x in label for x in ['status', 'state', 'priority', 'phase']):
                status[label] = path
            else:
                other[label] = path
        
        return {
            "status": "ok",
            "mappings": {
                "identity_fields": identity,
                "date_fields": dates,
                "contact_fields": contacts,
                "financial_fields": financial,
                "text_fields": text,
                "status_fields": status,
                "other_fields": other
            },
            "token_formats": {
                "text": "[Attribute(FieldPath)]",
                "date": "[Date(Source=Attribute,Path=FieldPath,Format=\"d\")]",
                "currency": "[Currency(Source=Attribute,Path=FieldPath,Format=\"C2\")]",
            },
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ============== Collect DOCX Injection tools ==============

DOCX_INJECTION_TOOLS = [
    analyze_uploaded_template,
    inject_tokens_into_template,
    show_token_mapping_guide,
]


# ============== Direct DOCX Processing Tools (Chat Attachments) ==============

@tool
def process_attached_docx(
    docx_base64: str,
    entity_def: str = "",
    filename: str = "attached_template.docx"
) -> dict:
    """
    Process a DOCX file attached directly in chat.
    
    Use this when a user attaches a Word document in the chat - you'll receive
    the file content as base64. This tool analyzes it for placeholder patterns
    and suggests Kahua tokens.
    
    Args:
        docx_base64: Base64-encoded DOCX file content (from chat attachment)
        entity_def: Target entity (e.g., "RFI", "Invoice", "kahua_AEC_RFI.RFI")
        filename: Original filename for reference
        
    Returns:
        Dict with analysis results and filename for follow-up actions
    """
    import base64
    try:
        from report_genius.injection import analyze_and_inject
        
        # Decode base64 content
        try:
            doc_bytes = base64.b64decode(docx_base64)
        except Exception:
            return {"status": "error", "message": "Invalid base64 content. Ensure the file is properly encoded."}
        
        # Validate it's a valid DOCX (should start with PK zip header)
        if not doc_bytes.startswith(b'PK'):
            return {"status": "error", "message": "Invalid DOCX file. The content does not appear to be a valid Word document."}
        
        # Save to uploads for subsequent processing
        saved_filename = f"chat_{filename}" if not filename.startswith("chat_") else filename
        uploads_dir = _get_uploads_dir()
        file_path = uploads_dir / saved_filename
        file_path.write_bytes(doc_bytes)
        
        # Resolve entity alias
        resolved_entity = resolve_entity_def(entity_def) if entity_def else ""
        
        # Analyze the document
        result = analyze_and_inject(doc_bytes, entity_def=resolved_entity, auto_inject=False)
        
        return {
            "status": "ok",
            "filename": saved_filename,
            "saved_to": str(file_path),
            "entity_def": resolved_entity or "(auto-detect)",
            "analysis": result['analysis'],
            "next_steps": [
                f"To inject tokens: inject_tokens_into_template('{saved_filename}', '{resolved_entity}')",
                f"For full template: analyze_and_complete_template('{saved_filename}', '{resolved_entity}', 'My Template')",
            ]
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@tool
def complete_attached_template(
    docx_base64: str,
    entity_def: str,
    template_name: str = "Imported Template",
    filename: str = "attached_template.docx"
) -> dict:
    """
    Complete an attached DOCX template with Kahua tokens and modern features.
    
    This is the full agentic completion tool for chat attachments. It:
    1. Decodes and saves the attached DOCX
    2. Analyzes semantic structure (sections, lists, tables)
    3. Creates a complete PortableViewTemplate with all features
    4. Saves and returns the template ID for rendering
    
    Use this when a user attaches a Word document and wants it fully converted
    to a Kahua-ready template with page headers/footers, lists, etc.
    
    Args:
        docx_base64: Base64-encoded DOCX file content (from chat attachment)
        entity_def: Target entity (e.g., "RFI", "Invoice")
        template_name: Name for the generated template
        filename: Original filename for reference
        
    Returns:
        Dict with template_id ready for render_completed_template()
    """
    import base64
    try:
        from agentic_template_analyzer import analyze_and_convert
        from report_genius.templates import PortableViewTemplate
        from report_genius.config import TEMPLATES_DIR
        
        # Decode base64 content
        try:
            doc_bytes = base64.b64decode(docx_base64)
        except Exception:
            return {"status": "error", "message": "Invalid base64 content"}
        
        if not doc_bytes.startswith(b'PK'):
            return {"status": "error", "message": "Invalid DOCX file"}
        
        # Save to uploads
        saved_filename = f"chat_{filename}" if not filename.startswith("chat_") else filename
        uploads_dir = _get_uploads_dir()
        file_path = uploads_dir / saved_filename
        file_path.write_bytes(doc_bytes)
        
        # Resolve entity alias
        resolved_entity = resolve_entity_def(entity_def)
        
        # Analyze and convert
        result = analyze_and_convert(doc_bytes, resolved_entity, template_name)
        
        if result.get('status') == 'ok':
            TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
            
            template = PortableViewTemplate.model_validate(result['template'])
            json_path = TEMPLATES_DIR / f"{template.id}.json"
            json_path.write_text(template.model_dump_json(indent=2))
            
            result['saved_to'] = str(json_path)
            result['original_file'] = saved_filename
            result['message'] = f"Template '{template_name}' created with {len(template.sections)} sections. Call render_completed_template('{template.id}') to generate DOCX."
        
        return result
    except Exception as e:
        return {"status": "error", "message": str(e)}


DIRECT_DOCX_TOOLS = [
    process_attached_docx,
    complete_attached_template,
]


# ============== Agentic Template Completion Tools ==============

@tool
def analyze_and_complete_template(
    filename: str,
    entity_def: str,
    template_name: str = "Imported Template"
) -> dict:
    """
    Analyze an uploaded DOCX and create a complete PortableViewTemplate.
    
    This is the AGENTIC template completion tool. It:
    1. Parses the document's semantic structure
    2. Detects blank/placeholder patterns and maps them to Kahua fields
    3. Generates a complete PortableViewTemplate
    
    Args:
        filename: Name of uploaded file (in uploads/ directory)
        entity_def: Kahua entity definition (e.g., "kahua_AEC_RFI.RFI")
        template_name: Name for the generated template
        
    Returns:
        Dict with analysis, template_id, and sections_summary
    """
    try:
        from agentic_template_analyzer import analyze_and_convert
        from report_genius.templates import PortableViewTemplate
        from report_genius.config import TEMPLATES_DIR
        
        file_path = _get_uploads_dir() / filename
        if not file_path.exists():
            return {"status": "error", "message": f"File not found: {filename}"}
        
        doc_bytes = file_path.read_bytes()
        result = analyze_and_convert(doc_bytes, entity_def, template_name)
        
        if result.get('status') == 'ok':
            TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
            
            template = PortableViewTemplate.model_validate(result['template'])
            json_path = TEMPLATES_DIR / f"{template.id}.json"
            json_path.write_text(template.model_dump_json(indent=2))
            
            result['saved_to'] = str(json_path)
            result['message'] = f"Template '{template_name}' created with {len(template.sections)} sections"
        
        return result
    except Exception as e:
        return {"status": "error", "message": str(e)}


@tool
def render_completed_template(
    template_id: str,
    output_name: str = None,
    add_page_header: bool = True,
    add_page_footer: bool = True
) -> dict:
    """
    Render a completed template to DOCX with full features.
    
    Args:
        template_id: ID from analyze_and_complete_template
        output_name: Optional custom filename
        add_page_header: Include page header if not already present
        add_page_footer: Include page footer with page numbers
        
    Returns:
        Dict with download URL for the rendered document
    """
    try:
        from report_genius.templates import PortableViewTemplate, PageHeaderFooterConfig
        from report_genius.rendering import DocxRenderer
        from report_genius.config import TEMPLATES_DIR, REPORTS_DIR
        
        json_path = TEMPLATES_DIR / f"{template_id}.json"
        
        if not json_path.exists():
            return {"status": "error", "message": f"Template {template_id} not found"}
        
        template = PortableViewTemplate.model_validate_json(json_path.read_text())
        
        if add_page_header and not template.layout.page_header:
            template.layout.page_header = PageHeaderFooterConfig(
                left_text=template.name,
                font_size=10,
            )
        
        if add_page_footer and not template.layout.page_footer:
            template.layout.page_footer = PageHeaderFooterConfig(
                include_page_number=True,
                page_number_format="Page {page} of {total}",
                font_size=9,
            )
        
        renderer = DocxRenderer(template)
        doc_bytes = renderer.render_to_bytes()
        
        REPORTS_DIR.mkdir(exist_ok=True)
        
        filename = output_name or template_id
        docx_path = REPORTS_DIR / f"{filename}.docx"
        docx_path.write_bytes(doc_bytes)
        
        base_url = os.getenv("REPORT_BASE_URL", "http://localhost:8000")
        
        return {
            "status": "ok",
            "filename": docx_path.name,
            "download_url": f"{base_url}/reports/{docx_path.name}",
            "template_name": template.name,
            "sections_rendered": len(template.sections),
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ============== Collect Agentic Template tools ==============

AGENTIC_TEMPLATE_TOOLS = [
    analyze_and_complete_template,
    render_completed_template,
]


# ============== Legacy Template Tools (Optional) ==============

def load_legacy_pv_tools():
    """Load legacy portable view tools if available."""
    tools = []
    try:
        from pv_md_renderer import preview_portable_view, finalize_portable_view, list_md_templates
        
        @tool
        def preview_md_portable_view(template_id: str, entity_data_json: str) -> dict:
            """Preview a portable view using an EXISTING template as rendered markdown."""
            try:
                entity_data = json.loads(entity_data_json)
                return preview_portable_view(template_id, entity_data)
            except Exception as e:
                return {"status": "error", "message": str(e)}
        
        @tool
        def finalize_md_portable_view(preview_id: str) -> dict:
            """Finalize a previewed portable view and generate the DOCX."""
            return finalize_portable_view(preview_id)
        
        @tool
        def list_md_templates_tool() -> dict:
            """List available markdown portable view templates."""
            return list_md_templates()
        
        tools = [preview_md_portable_view, finalize_md_portable_view, list_md_templates_tool]
        log.info("Legacy PV tools loaded")
    except ImportError:
        log.warning("Legacy PV tools not available")
    
    return tools


def load_legacy_template_gen_tools():
    """Load legacy template generation tools if available."""
    tools = []
    try:
        from pv_template_generator import (
            create_entity_template,
            preview_template,
            finalize_preview,
            save_template,
            load_template,
            list_saved_templates,
            update_template_markdown,
        )
        
        @tool
        def create_template_for_entity(
            entity_def: str,
            entity_display_name: str,
            schema_fields_json: str,
            style: str = "professional"
        ) -> dict:
            """Create a NEW reusable template for any entity type (legacy)."""
            try:
                schema_fields = json.loads(schema_fields_json)
                return create_entity_template(
                    entity_def=entity_def,
                    entity_display_name=entity_display_name,
                    schema_fields=schema_fields,
                    style=style,
                )
            except Exception as e:
                return {"status": "error", "message": str(e)}
        
        @tool
        def preview_custom_template(
            template_id: str,
            template_markdown: str,
            entity_data_json: str
        ) -> dict:
            """Preview a custom template with actual entity data (legacy)."""
            try:
                entity_data = json.loads(entity_data_json)
                return preview_template(template_id, template_markdown, entity_data)
            except Exception as e:
                return {"status": "error", "message": str(e)}
        
        @tool
        def finalize_custom_template(preview_id: str, output_name: str = None) -> dict:
            """Generate DOCX from a previewed custom template (legacy)."""
            return finalize_preview(preview_id, output_name)
        
        @tool
        def save_custom_template(
            template_id: str,
            name: str,
            entity_def: str,
            markdown: str,
            description: str = ""
        ) -> dict:
            """Save a custom template for future reuse (legacy)."""
            return save_template(template_id, name, entity_def, markdown, description)
        
        @tool
        def list_custom_templates(entity_def: str = None) -> dict:
            """List saved custom templates (legacy)."""
            return list_saved_templates(entity_def)
        
        @tool
        def modify_template(template_id: str, new_markdown: str) -> dict:
            """Update the markdown content of a template (legacy)."""
            return update_template_markdown(template_id, new_markdown)
        
        tools = [
            create_template_for_entity,
            preview_custom_template,
            finalize_custom_template,
            save_custom_template,
            list_custom_templates,
            modify_template,
        ]
        log.info("Legacy template gen tools loaded")
    except ImportError as e:
        log.warning(f"Legacy template gen tools not available: {e}")
    
    return tools


# ============== All Tools Aggregator ==============

def get_all_tools():
    """Get all available tools for the agent."""
    legacy_tools = []
    if os.getenv("RG_ENABLE_LEGACY_TOOLS", "").strip().lower() in {"1", "true", "yes"}:
        legacy_tools = load_legacy_pv_tools() + load_legacy_template_gen_tools()

    all_tools = (
        KAHUA_API_TOOLS +
        SOTA_TEMPLATE_TOOLS +
        DOCX_INJECTION_TOOLS +
        DIRECT_DOCX_TOOLS +
        AGENTIC_TEMPLATE_TOOLS +
        legacy_tools
    )
    log.info(f"Loaded {len(all_tools)} agent tools")
    return all_tools


def get_tools_by_mode(mode: str):
    """Return a focused toolset for the given mode."""
    legacy_tools = []
    if os.getenv("RG_ENABLE_LEGACY_TOOLS", "").strip().lower() in {"1", "true", "yes"}:
        legacy_tools = load_legacy_pv_tools() + load_legacy_template_gen_tools()

    if mode == "injection":
        return DOCX_INJECTION_TOOLS + DIRECT_DOCX_TOOLS
    if mode == "template":
        return SOTA_TEMPLATE_TOOLS + AGENTIC_TEMPLATE_TOOLS + legacy_tools
    if mode == "analytics":
        return KAHUA_API_TOOLS
    return get_all_tools()
