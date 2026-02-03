"""
LangGraph-based Kahua Construction Analyst Agent

Uses Claude via Azure with LangChain/LangGraph for native Anthropic support.
"""

import os
import json
import logging
from typing import Any, Dict, List, Optional, Annotated, TypedDict
from pathlib import Path

import httpx
from dotenv import load_dotenv

# Load environment before imports that need it
load_dotenv()

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

# Report generation
from report_generator import create_report

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("langgraph_agent")

# ============== Configuration ==============

AZURE_ENDPOINT = os.environ.get("AZURE_ENDPOINT", "").rstrip("/")
AZURE_KEY = os.environ.get("AZURE_KEY", "")
MODEL_DEPLOYMENT = os.environ.get("AZURE_DEPLOYMENT", "claude-sonnet-4-5")

# Kahua API
QUERY_URL_TEMPLATE = "https://demo01service.kahua.com/v2/domains/Summit/projects/{project_id}/query?returnDefaultAttributes=true"
KAHUA_BASIC_AUTH = os.getenv("KAHUA_BASIC_AUTH")

def _auth_header_value() -> str:
    if not KAHUA_BASIC_AUTH:
        raise RuntimeError("KAHUA_BASIC_AUTH not set")
    return KAHUA_BASIC_AUTH if KAHUA_BASIC_AUTH.strip().lower().startswith("basic ") \
           else f"Basic {KAHUA_BASIC_AUTH}"

HEADERS_JSON = lambda: {"Content-Type": "application/json", "Authorization": _auth_header_value()}

# Entity aliases
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
    key = (name_or_def or "").strip().lower()
    return ENTITY_ALIASES.get(key, name_or_def)


# ============== Tools ==============

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
    
    ╔══════════════════════════════════════════════════════════════════════╗
    ║ ⚠️  THIS IS NOT FOR TEMPLATES!                                        ║
    ║     For templates/portable views → use build_custom_template          ║
    ╚══════════════════════════════════════════════════════════════════════╝
    
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
    
    ✅ USE FOR:
        - "Show me all overdue RFIs" → analytics report
        - "Summarize contract spending" → data report
        
    ❌ DO NOT USE FOR:
        - "Create an RFI template" → use build_custom_template instead
        - "Build a portable view" → use build_custom_template instead
    """
    try:
        charts = json.loads(charts_json) if charts_json else None
        result = create_report(title=title, markdown_content=markdown_content, charts=charts, subtitle=subtitle)
        filename = result["filename"]
        base_url = os.getenv("REPORT_BASE_URL", "http://localhost:8000")
        return {"status": "ok", "filename": filename, "download_url": f"{base_url}/reports/{filename}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# Portable view tools - Static templates
try:
    from pv_md_renderer import preview_portable_view, finalize_portable_view, list_md_templates
    
    @tool
    def preview_md_portable_view(template_id: str, entity_data_json: str) -> dict:
        """
        Preview a portable view using an EXISTING template as rendered markdown.
        For creating NEW custom templates, use create_entity_template instead.
        
        Args:
            template_id: Template name (e.g., "contract", "rfi", "punchlist")
            entity_data_json: JSON string of entity data from query_entities
        
        Returns:
            Dict with preview_id and rendered markdown to display in chat.
        """
        try:
            entity_data = json.loads(entity_data_json)
            return preview_portable_view(template_id, entity_data)
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    @tool
    def finalize_md_portable_view(preview_id: str) -> dict:
        """
        Finalize a previewed portable view and generate the DOCX.
        Only call AFTER user approves the preview.
        
        Args:
            preview_id: The preview_id from preview_md_portable_view
        
        Returns:
            Dict with download URL for the generated document.
        """
        return finalize_portable_view(preview_id)
    
    @tool
    def list_md_templates_tool() -> dict:
        """List available markdown portable view templates."""
        return list_md_templates()
    
    pv_tools = [preview_md_portable_view, finalize_md_portable_view, list_md_templates_tool]
    log.info("Portable view tools loaded")
except ImportError:
    pv_tools = []
    log.warning("Portable view tools not available")


# Dynamic Template Creation Tools
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
        """
        Create a NEW reusable template for any entity type.
        Use this when user wants a custom portable view for an entity.
        
        WORKFLOW:
        1. Call get_entity_schema to get field info
        2. Call this tool to generate template
        3. Call preview_custom_template to show preview with real data
        4. Iterate based on feedback
        5. Call save_custom_template when approved
        
        Args:
            entity_def: Full entity definition (e.g., "kahua_AEC_RFI.RFI")
            entity_display_name: Human-readable name (e.g., "RFI", "Contract")
            schema_fields_json: JSON string of fields from get_entity_schema
            style: "professional", "simple", or "detailed"
        
        Returns:
            Dict with template_id and markdown content
        """
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
        """
        Preview a custom template with actual entity data.
        Display the rendered markdown to the user for feedback.
        
        Args:
            template_id: Template identifier from create_template_for_entity
            template_markdown: The markdown template content
            entity_data_json: JSON string of entity data to render
        
        Returns:
            Dict with preview_id and rendered markdown
        """
        try:
            entity_data = json.loads(entity_data_json)
            return preview_template(template_id, template_markdown, entity_data)
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    @tool
    def finalize_custom_template(preview_id: str, output_name: str = None) -> dict:
        """
        Generate DOCX from a previewed custom template.
        Call after user approves the preview.
        
        Args:
            preview_id: Preview ID from preview_custom_template
            output_name: Optional custom filename (without extension)
        
        Returns:
            Dict with download URL
        """
        return finalize_preview(preview_id, output_name)
    
    @tool
    def save_custom_template(
        template_id: str,
        name: str,
        entity_def: str,
        markdown: str,
        description: str = ""
    ) -> dict:
        """
        Save a custom template for future reuse.
        Call after user approves the template design.
        
        Args:
            template_id: Template identifier
            name: Human-readable template name
            entity_def: Target entity definition
            markdown: The markdown template content
            description: Optional description
        
        Returns:
            Dict with save status
        """
        return save_template(template_id, name, entity_def, markdown, description)
    
    @tool
    def list_custom_templates(entity_def: str = None) -> dict:
        """
        List saved custom templates.
        
        Args:
            entity_def: Optional filter by entity type
        
        Returns:
            Dict with list of saved templates
        """
        return list_saved_templates(entity_def)
    
    @tool
    def modify_template(template_id: str, new_markdown: str) -> dict:
        """
        Update the markdown content of a template based on user feedback.
        
        Args:
            template_id: Template or preview ID to update
            new_markdown: Updated markdown content
        
        Returns:
            Dict with updated preview
        """
        return update_template_markdown(template_id, new_markdown)
    
    template_gen_tools = [
        create_template_for_entity,
        preview_custom_template,
        finalize_custom_template,
        save_custom_template,
        list_custom_templates,
        modify_template,
    ]
    log.info("Template generation tools loaded")
except ImportError as e:
    template_gen_tools = []
    log.warning(f"Template generation tools not available: {e}")


# ============== Unified SOTA Template Tools ==============

try:
    from unified_templates import get_unified_system
    
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
        system = get_unified_system()
        return {"status": "ok", "archetypes": system.get_archetypes()}
    
    @tool
    def list_template_entities() -> dict:
        """
        List entity types available for SOTA template generation.
        
        These are pre-analyzed entity schemas with intelligent field categorization.
        
        Returns:
            Dict with list of entities and their field counts
        """
        system = get_unified_system()
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
        
        PREFERRED OVER create_template_for_entity for better quality.
        
        Args:
            entity_type: Entity type (e.g., "Invoice", "RFI", "ExpenseContract")
            archetype: Optional design pattern ("financial_report", "correspondence", etc.)
                      Auto-inferred if not provided.
            user_intent: Natural language description (e.g., "executive summary for board")
            name: Custom template name
        
        Returns:
            Dict with template structure and sections summary
        
        Example usage:
            smart_compose_template("Invoice", "financial_report", "payment summary for approval")
            smart_compose_template("RFI", user_intent="formal response letter")
        """
        try:
            system = get_unified_system()
            template = system.compose_smart(
                entity_type=entity_type,
                archetype=archetype,
                user_intent=user_intent,
                name=name,
            )
            
            # Save to disk
            from report_genius.config import TEMPLATES_DIR
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
            from pathlib import Path
            from report_genius.templates import PortableViewTemplate
            from report_genius.config import TEMPLATES_DIR, REPORTS_DIR
            
            # Find template
            json_path = TEMPLATES_DIR / f"{template_id}.json"
            
            if not json_path.exists():
                return {"status": "error", "message": f"Template {template_id} not found"}
            
            # Load and render
            template = PortableViewTemplate.model_validate_json(json_path.read_text())
            system = get_unified_system()
            
            REPORTS_DIR.mkdir(exist_ok=True)
            
            filename = output_name or template_id
            docx_path = REPORTS_DIR / f"{filename}.docx"
            system.render_to_docx(template, docx_path)
            
            import os
            base_url = os.getenv("REPORT_BASE_URL", "http://localhost:8000")
            
            return {
                "status": "ok",
                "filename": docx_path.name,
                "download_url": f"{base_url}/reports/{docx_path.name}",
                "template_name": template.name,
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    # Storage for templates being built interactively
    _active_templates: Dict[str, dict] = {}
    
    @tool
    def get_template_fields(entity_type: str, category: str = None) -> dict:
        """
        Show all available fields for an entity type from the template generation system.
        
        This uses the built-in template schemas. For live Kahua schema data, use
        get_entity_fields() from the schema service instead.
        
        Args:
            entity_type: Entity type (e.g., "Invoice", "RFI", "ExpenseContract")
            category: Optional filter - "identity", "financial", "date", "contact", 
                     "text_block", "status", "collection", etc.
        
        Returns:
            Dict with fields organized by category, with labels and suggested formats
        """
        try:
            system = get_unified_system()
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
                    # For list type:
                    "list_type": "bullet" | "number",
                    "items": ["Item 1", "Item 2 with {Field}"]
                }
            include_logo: Whether to include company logo placeholder
            layout: "single_column" or "two_column"
            static_title: A literal text title to display (e.g., "Beaus RFI Template")
                         This is NOT a placeholder - it appears as-is in the document.
            title_style_json: JSON object for title styling:
                {
                    "font": "Comic Sans MS",  // Font family
                    "size": 28,               // Point size
                    "color": "#0000FF",       // Hex color (blue)
                    "bold": true,             // Bold toggle
                    "alignment": "center"     // left, center, right
                }
            page_header_json: JSON object for page header:
                {
                    "left_text": "Company Name",
                    "center_text": "CONFIDENTIAL",
                    "right_text": "Report ID",
                    "include_page_number": false,
                    "font_size": 9
                }
            page_footer_json: JSON object for page footer:
                {
                    "left_text": "Generated by Report Genius",
                    "center_text": null,
                    "right_text": null,
                    "include_page_number": true,
                    "page_number_format": "Page {page} of {total}",
                    "font_size": 9
                }
        
        Returns:
            Dict with template_id and structure summary
        
        Example:
            User: "Create an RFI template called 'Beaus RFI Template' in Comic Sans, blue, size 28"
            -> build_custom_template(
                "RFI", 
                "Beaus RFI Template",
                '[{"type": "detail", "fields": ["Number", "Subject", "Status"]}]',
                static_title="Beaus RFI Template",
                title_style_json='{"font": "Comic Sans MS", "size": 28, "color": "#0000FF"}'
               )
        """
        try:
            import json as json_module
            import uuid
            from report_genius.templates import (
                PortableViewTemplate, Section, SectionType,
                HeaderConfig, DetailConfig, TableConfig, TextConfig, ListConfig,
                FieldDef, FieldFormat as TGFieldFormat, TableColumn,
                LayoutConfig, PageHeaderFooterConfig,
            )
            
            system = get_unified_system()
            
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
            sections_spec = json_module.loads(sections_json)
            
            # Build field lookup for format hints
            field_lookup = {f.path: f for f in schema.fields}
            field_lookup.update({f.path.lower(): f for f in schema.fields})
            field_lookup.update({f.label.lower(): f for f in schema.fields})
            
            def resolve_field(field_name: str) -> FieldDef:
                """Resolve a field name to FieldDef with proper formatting."""
                # Try exact match first
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
                # Fallback to using the name directly
                return FieldDef(path=field_name, label=field_name.replace("_", " ").title(), format=TGFieldFormat.TEXT)
            
            # Build sections
            built_sections = []
            has_header = any(spec.get("type") == "header" for spec in sections_spec)
            
            # Auto-create header section if none specified and logo is requested
            if not has_header and include_logo:
                # Find best title field (Number, Subject, or first identity field)
                title_field_path = "Number"  # Default
                subtitle_field_path = "Subject"  # Default subtitle
                
                for f in schema.fields:
                    if f.category.value == "identity":
                        if f.path.lower() in ["number", "id", "reference"]:
                            title_field_path = f.path
                        elif f.path.lower() in ["subject", "name", "title", "description"]:
                            subtitle_field_path = f.path
                
                # Parse title style if provided
                title_style = {}
                if title_style_json:
                    try:
                        title_style = json_module.loads(title_style_json)
                    except:
                        pass
                
                # Map alignment string to enum
                from report_genius.templates import Alignment
                align_map = {"left": Alignment.LEFT, "center": Alignment.CENTER, "right": Alignment.RIGHT}
                title_alignment = align_map.get(title_style.get("alignment", "left"), Alignment.LEFT)
                
                auto_header = HeaderConfig(
                    title_template=f"{{{title_field_path}}}",
                    subtitle_template=f"{{{subtitle_field_path}}}",
                    fields=[],
                    show_logo=True,
                    # Custom styling
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
                
                # Adjust order if we auto-added a header
                section_order = idx + 1 if (not has_header and include_logo) else idx
                
                if sec_type == SectionType.HEADER:
                    # Header section
                    field_defs = [resolve_field(f) for f in fields]
                    title_field = field_defs[0] if field_defs else None
                    
                    # Parse title style if provided (and not already parsed)
                    if 'title_style' not in dir():
                        title_style = {}
                        if title_style_json:
                            try:
                                title_style = json_module.loads(title_style_json)
                            except:
                                pass
                        from report_genius.templates import Alignment
                        align_map = {"left": Alignment.LEFT, "center": Alignment.CENTER, "right": Alignment.RIGHT}
                        title_alignment = align_map.get(title_style.get("alignment", "left"), Alignment.LEFT)
                    
                    config = HeaderConfig(
                        title_template=f"{{{title_field.path}}}" if title_field else "{Number}",
                        subtitle_template=f"{{{field_defs[1].path}}}" if len(field_defs) > 1 else None,
                        fields=field_defs[2:] if len(field_defs) > 2 else [],
                        show_logo=include_logo,
                        # Custom styling
                        static_title=static_title,
                        title_font=title_style.get("font") if title_style else None,
                        title_size=title_style.get("size") if title_style else None,
                        title_color=title_style.get("color") if title_style else None,
                        title_bold=title_style.get("bold", True) if title_style else True,
                        title_alignment=title_alignment if 'title_alignment' in dir() else Alignment.LEFT,
                    )
                    built_sections.append(Section(
                        type=SectionType.HEADER, order=section_order, header_config=config
                    ))
                    
                elif sec_type == SectionType.DETAIL:
                    # Detail section with field grid
                    field_defs = [resolve_field(f) for f in fields]
                    # Apply bold formatting
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
                    # Table section for collections
                    source = spec.get("source", fields[0] if fields else "Items")
                    columns = [
                        TableColumn(field=resolve_field(f))
                        for f in fields
                    ]
                    config = TableConfig(source=source, columns=columns, show_header=True)
                    built_sections.append(Section(
                        type=SectionType.TABLE, title=title, order=section_order, table_config=config
                    ))
                    
                elif sec_type == SectionType.TEXT:
                    # Text/content section
                    content = spec.get("content", "")
                    if not content and fields:
                        # Use fields as content blocks
                        content = "\n\n".join(f"{{{f}}}" for f in fields)
                    config = TextConfig(content=content)
                    built_sections.append(Section(
                        type=SectionType.TEXT, title=title, order=section_order, text_config=config
                    ))
                    
                elif sec_type == SectionType.LIST:
                    # List section (bullet or numbered)
                    list_type = spec.get("list_type", "bullet")
                    items = spec.get("items", fields)  # Use items if specified, otherwise fields as items
                    config = ListConfig(list_type=list_type, items=items)
                    built_sections.append(Section(
                        type=SectionType.LIST, title=title, order=section_order, list_config=config
                    ))
            
            # Parse page header/footer configs
            page_header_config = None
            if page_header_json:
                try:
                    ph_data = json_module.loads(page_header_json)
                    page_header_config = PageHeaderFooterConfig(**ph_data)
                except:
                    pass
            
            page_footer_config = None
            if page_footer_json:
                try:
                    pf_data = json_module.loads(page_footer_json)
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
            
            # Save to disk and active templates
            from report_genius.config import TEMPLATES_DIR
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
        
        Use this when user asks to change something about a template you've created:
        - "remove the logo"
        - "make the subject bold"
        - "add the Due Date field"
        - "remove the financial section"
        
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
            config_json: JSON config for the operation:
                - add_fields: {"section_index": 0, "fields": ["Field1", "Field2"]}
                - remove_fields: {"section_index": 0, "fields": ["Field1"]}
                - add_section: {"type": "detail", "title": "New Section", "fields": [...], "position": 1}
                - remove_section: {"section_index": 2}
                - toggle_logo: {"show": false}
                - set_bold: {"fields": ["Subject", "Description"]}
                - set_columns: {"section_index": 0, "columns": 2}
        
        Returns:
            Dict with updated template structure
        """
        try:
            import json as json_module
            from pathlib import Path
            from report_genius.templates import (
                PortableViewTemplate, Section, SectionType,
                HeaderConfig, DetailConfig, FieldDef, FieldFormat as TGFieldFormat,
            )
            
            # Load template
            from report_genius.config import TEMPLATES_DIR
            json_path = TEMPLATES_DIR / f"{template_id}.json"
            
            if not json_path.exists():
                return {"status": "error", "message": f"Template {template_id} not found"}
            
            template = PortableViewTemplate.model_validate_json(json_path.read_text())
            config = json_module.loads(config_json) if config_json else {}
            
            system = get_unified_system()
            
            # Find schema for field resolution
            schema = None
            for key, s in system.tg_schemas.items():
                if s.entity_def == template.entity_def:
                    schema = s
                    break
            
            if operation == "toggle_logo":
                # Find header section and toggle logo
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
                    # Reorder
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
        
        Use this to show the user what their template contains before rendering.
        
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
            
            # Build detailed structure
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
    
    unified_template_tools = [
        list_template_archetypes,
        list_template_entities,
        smart_compose_template,
        render_smart_template,
        get_template_fields,
        build_custom_template,
        modify_existing_template,
        preview_template_structure,
    ]
    log.info("Unified SOTA template tools loaded (including interactive tools)")
except ImportError as e:
    unified_template_tools = []
    log.warning(f"Unified template tools not available: {e}")


# ============== DOCX Token Injection Tools ==============

try:
    from docx_token_injector import (
        analyze_and_inject, 
        add_logo_placeholder, 
        add_timestamp_token,
        LABEL_NORMALIZATIONS
    )
    from pathlib import Path
    
    UPLOADS_DIR = Path(__file__).parent / "uploads"
    UPLOADS_DIR.mkdir(exist_ok=True)
    
    @tool
    def analyze_uploaded_template(filename: str, entity_def: str = "") -> dict:
        """
        Analyze an uploaded DOCX template and detect placeholder patterns.
        
        This tool examines a Word document that may have "blank" template patterns like:
        - "ID: " (label with trailing whitespace - expects a value)
        - "Status: ______" (label with underscores)
        - "Date: [blank]" or "Date: <value>"
        
        The AI detects these patterns and suggests appropriate Kahua tokens to inject.
        
        WORKFLOW:
        1. User uploads a template via /upload endpoint
        2. Call this tool with the filename to analyze it
        3. Review the detected placeholders with the user
        4. Call inject_tokens_into_template to add the tokens
        
        Args:
            filename: The uploaded file name (in uploads/ directory)
            entity_def: Target Kahua entity (e.g., "kahua_AEC_RFI.RFI") for better field mapping
            
        Returns:
            Dict with:
            - placeholders: List of detected label→token mappings with confidence scores
            - suggestions: Recommendations for additional fields
            - document_summary: Stats about the document structure
        """
        try:
            file_path = UPLOADS_DIR / filename
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
        add_logo: bool = False,
        add_timestamp: bool = False
    ) -> dict:
        """
        Inject Kahua tokens into an uploaded template based on detected patterns.
        
        IMPORTANT: This tool PRESERVES the user's existing document layout.
        It only replaces detected blank/placeholder areas with Kahua tokens.
        It does NOT add new elements like logos or footers by default.
        
        The tool will:
        1. Re-analyze the document to find placeholder patterns
        2. Replace blank areas with appropriate Kahua tokens
        3. Preserve ALL existing formatting, images, and layout
        
        Args:
            filename: The uploaded file name to modify
            entity_def: Target Kahua entity for better field mapping
            add_logo: ONLY set True if user explicitly requests adding a logo (default False)
            add_timestamp: ONLY set True if user explicitly requests a timestamp (default False)
            
        Returns:
            Dict with:
            - modified_filename: New file with tokens injected
            - download_url: URL to download the modified template
            - tokens_injected: Number of tokens added
            - changes: List of changes made
        """
        try:
            import os
            
            file_path = UPLOADS_DIR / filename
            if not file_path.exists():
                return {"status": "error", "message": f"File not found: {filename}"}
            
            doc_bytes = file_path.read_bytes()
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
            
            # Save modified document - ensure clean filename
            from urllib.parse import quote
            
            # Handle double-tokenized filenames
            base_filename = filename
            if base_filename.startswith("tokenized_"):
                base_filename = base_filename[10:]  # Remove existing prefix
            
            modified_filename = f"tokenized_{base_filename}"
            modified_path = UPLOADS_DIR / modified_filename
            modified_path.write_bytes(modified_doc)
            
            # Also copy to reports for download
            reports_dir = Path(__file__).parent / "reports"
            reports_dir.mkdir(exist_ok=True)
            (reports_dir / modified_filename).write_bytes(modified_doc)
            
            base_url = os.getenv("REPORT_BASE_URL", "http://localhost:8000")
            # URL-encode the filename for proper linking
            encoded_filename = quote(modified_filename)
            
            return {
                "status": "ok",
                "original_filename": filename,
                "modified_filename": modified_filename,
                "download_url": f"{base_url}/reports/{encoded_filename}",
                "tokens_injected": result['injection']['tokens_injected'],
                "changes": result['injection']['changes_made'],
                "aesthetics_added": aesthetics_added,
                "warnings": result['injection'].get('warnings', [])
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    @tool
    def show_token_mapping_guide() -> dict:
        """
        Show the label-to-token mapping guide.
        
        Returns the mapping rules used to convert labels like "ID:" or "Status:"
        to their corresponding Kahua attribute paths.
        
        Use this when a user wants to understand or customize how labels
        are mapped to Kahua tokens, or when they want to add custom mappings.
        
        Returns:
            Dict with common label mappings organized by category
        """
        # Organize mappings by category
        identity = {}
        dates = {}
        contacts = {}
        financial = {}
        text = {}
        status = {}
        other = {}
        
        for label, path in LABEL_NORMALIZATIONS.items():
            path_lower = path.lower()
            if any(x in label for x in ['id', 'number', 'name', 'subject', 'title', 'ref']):
                identity[label] = path
            elif any(x in label for x in ['date', 'due', 'start', 'end', 'created', 'modified', 'submitted', 'required']):
                dates[label] = path
            elif any(x in label for x in ['from', 'to', 'by', 'author', 'contact', 'company', 'contractor', 'vendor', 'assigned']):
                contacts[label] = path
            elif any(x in label for x in ['amount', 'cost', 'price', 'total', 'value']):
                financial[label] = path
            elif any(x in label for x in ['description', 'notes', 'scope', 'question', 'answer', 'comment']):
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
                "number": "[Number(Source=Attribute,Path=FieldPath,Format=\"N0\")]",
                "logo": "[CompanyLogo(Height=60,Width=60)]",
                "timestamp": "[ReportModifiedTimeStamp]"
            },
            "tips": [
                "Labels are matched case-insensitively",
                "Compound labels like 'Due Date' are normalized to 'DueDate'",
                "Nested fields use dot notation: 'Status.Name', 'Author.ShortLabel'",
                "Custom mappings can be provided via the API"
            ]
        }
    
    # DEPRECATED: These regex-based tools are kept for backward compatibility
    # but are NOT included in the main agent tools list.
    # Use LLM-driven tools (analyze_template_with_llm, inject_tokens_with_llm) instead.
    _deprecated_docx_injection_tools = [
        analyze_uploaded_template,
        inject_tokens_into_template,
        show_token_mapping_guide,
    ]
    
    # Only expose the mapping guide (useful reference), not the deprecated analyzers
    docx_injection_tools = [show_token_mapping_guide]
    log.info("DOCX token injection tools loaded (regex tools deprecated)")
except ImportError as e:
    docx_injection_tools = []
    log.warning(f"DOCX injection tools not available: {e}")


# ============== LLM-Driven Template Analysis Tools ==============

try:
    from llm_injection_analyzer import (
        analyze_and_inject_with_llm,
        analyze_document_with_llm,
        inject_tokens_from_analysis,
    )
    
    @tool
    def analyze_template_with_llm(
        filename: str,
        entity_def: str = "",
    ) -> dict:
        """
        USE THIS TOOL for analyzing uploaded templates - it's smarter than regex.
        
        This tool uses Claude to intelligently analyze a DOCX template and identify
        ALL injection points, including complex patterns that regex misses:
        
        - Currency rows ending with just "$" (e.g., "Original Contract Sum    $")
        - Checkbox fields (☐ increased ☐ decreased ☐ unchanged)
        - Inline blanks within sentences (e.g., "unchanged by (   ) days")
        - Conditional text patterns
        - Date placeholders without obvious markers
        - Any area where dynamic data should appear
        
        The LLM understands context and semantics, so it can:
        - Infer correct field mappings from surrounding text
        - Detect patterns that don't follow standard "Label: value" format
        - Understand document domain (Change Orders, RFIs, Contracts, etc.)
        
        WORKFLOW:
        1. User uploads a template file
        2. Call this tool to get intelligent analysis
        3. Review the detected injection points with the user
        4. Call inject_tokens_with_llm to apply the changes
        
        Args:
            filename: The uploaded file name (in uploads/ directory)
            entity_def: Target Kahua entity for better field mapping
            
        Returns:
            Dict with:
            - document_summary: What the LLM understood about the document
            - entity_type_detected: Inferred entity type
            - injection_points: List of all detected injection locations with:
                - original_text: The text in the document
                - text_to_replace: What should be replaced
                - kahua_field_path: Suggested Kahua field
                - injection_type: currency/date/text/checkbox/etc.
                - token: The Kahua token to inject
                - reasoning: Why the LLM chose this mapping
            - suggestions: Recommendations for the template
        """
        try:
            file_path = UPLOADS_DIR / filename
            if not file_path.exists():
                return {"status": "error", "message": f"File not found: {filename}"}
            
            if not filename.lower().endswith(('.docx', '.doc')):
                return {"status": "error", "message": "Only Word documents (.docx) are supported"}
            
            doc_bytes = file_path.read_bytes()
            result = analyze_and_inject_with_llm(doc_bytes, entity_def=entity_def, auto_inject=False)
            
            if not result.get('success'):
                return {"status": "error", "message": result.get('error', 'Analysis failed')}
            
            return {
                "status": "ok",
                "filename": filename,
                "entity_def": entity_def or "(auto-detected)",
                "document_summary": result['analysis']['document_summary'],
                "entity_type_detected": result['analysis']['entity_type_detected'],
                "injection_points_count": len(result['analysis']['injection_points']),
                "injection_points": result['analysis']['injection_points'],
                "warnings": result['analysis']['warnings'],
                "suggestions": result['analysis']['suggestions'],
            }
        except Exception as e:
            import traceback
            return {"status": "error", "message": str(e), "trace": traceback.format_exc()}
    
    @tool
    def inject_tokens_with_llm(
        filename: str,
        entity_def: str = "",
        add_logo: bool = False,
        add_timestamp: bool = False
    ) -> dict:
        """
        Inject Kahua tokens into a template using LLM-detected injection points.
        
        This uses Claude to analyze the document and inject tokens into ALL
        detected locations, including complex patterns like:
        - Financial rows with "$" placeholders
        - Checkbox/boolean fields
        - Inline blanks within sentences
        - Conditional selections
        
        Unlike the regex-based injector, this handles edge cases and understands context.
        
        Args:
            filename: The uploaded file name to modify
            entity_def: Target Kahua entity for field mapping
            add_logo: Set True only if user explicitly requests a logo
            add_timestamp: Set True only if user explicitly requests a timestamp
            
        Returns:
            Dict with:
            - modified_filename: New file with tokens injected
            - download_url: URL to download the modified template
            - tokens_injected: Number of tokens added
            - changes: List of changes made
            - injection_points: Details of what was injected where
        """
        try:
            import os
            from urllib.parse import quote
            
            file_path = UPLOADS_DIR / filename
            if not file_path.exists():
                return {"status": "error", "message": f"File not found: {filename}"}
            
            doc_bytes = file_path.read_bytes()
            result = analyze_and_inject_with_llm(doc_bytes, entity_def=entity_def, auto_inject=True)
            
            if not result.get('success'):
                return {"status": "error", "message": result.get('error', 'Analysis failed')}
            
            modified_doc = result.get('modified_document', doc_bytes)
            aesthetics_added = []
            
            # Import add-on functions from original injector
            from docx_token_injector import add_logo_placeholder, add_timestamp_token
            
            if add_logo:
                modified_doc = add_logo_placeholder(modified_doc, position='header')
                aesthetics_added.append("company_logo")
            
            if add_timestamp:
                modified_doc = add_timestamp_token(modified_doc, position='footer')
                aesthetics_added.append("timestamp")
            
            # Clean filename
            base_filename = filename
            if base_filename.startswith("tokenized_"):
                base_filename = base_filename[10:]
            
            modified_filename = f"tokenized_{base_filename}"
            modified_path = UPLOADS_DIR / modified_filename
            modified_path.write_bytes(modified_doc)
            
            # Copy to reports for download
            reports_dir = Path(__file__).parent / "reports"
            reports_dir.mkdir(exist_ok=True)
            (reports_dir / modified_filename).write_bytes(modified_doc)
            
            base_url = os.getenv("REPORT_BASE_URL", "http://localhost:8000")
            encoded_filename = quote(modified_filename)
            
            return {
                "status": "ok",
                "original_filename": filename,
                "modified_filename": modified_filename,
                "download_url": f"{base_url}/reports/{encoded_filename}",
                "document_summary": result['analysis']['document_summary'],
                "tokens_injected": result['injection']['tokens_injected'],
                "changes": result['injection']['changes_made'],
                "injection_points": result['analysis']['injection_points'],
                "aesthetics_added": aesthetics_added,
                "warnings": result['analysis'].get('warnings', []),
                "suggestions": result['analysis'].get('suggestions', []),
            }
        except Exception as e:
            import traceback
            return {"status": "error", "message": str(e), "trace": traceback.format_exc()}
    
    llm_injection_tools = [
        analyze_template_with_llm,
        inject_tokens_with_llm,
    ]
    log.info("LLM-driven injection tools loaded")
except ImportError as e:
    llm_injection_tools = []
    log.warning(f"LLM injection tools not available: {e}")


# ============== Agentic Template Completion Tools ==============

try:
    from agentic_template_analyzer import analyze_and_convert, analyze_document
    from report_genius.rendering import DocxRenderer as SOTADocxRenderer
    from report_genius.templates import PortableViewTemplate
    
    @tool
    def analyze_and_complete_template(
        filename: str,
        entity_def: str,
        template_name: str = "Imported Template"
    ) -> dict:
        """
        Analyze an uploaded DOCX and create a complete PortableViewTemplate.
        
        This is the AGENTIC template completion tool. It:
        1. Parses the document's semantic structure (sections, lists, tables, headers)
        2. Detects blank/placeholder patterns and maps them to Kahua fields
        3. Extracts styling information (fonts, colors, alignment)
        4. Generates a complete PortableViewTemplate with all features
        
        USE THIS when a user uploads a "blank" template and wants it completed
        with Kahua tokens AND modern features like page headers/footers, lists, etc.
        
        Args:
            filename: Name of uploaded file (in uploads/ directory)
            entity_def: Kahua entity definition (e.g., "kahua_AEC_RFI.RFI")
            template_name: Name for the generated template
            
        Returns:
            Dict with:
            - analysis: What was detected in the document
            - template_id: ID of generated template (can be rendered)
            - sections_summary: Overview of generated sections
            - suggestions: Recommendations for improvements
        """
        try:
            file_path = UPLOADS_DIR / filename
            if not file_path.exists():
                return {"status": "error", "message": f"File not found: {filename}"}
            
            doc_bytes = file_path.read_bytes()
            result = analyze_and_convert(doc_bytes, entity_def, template_name)
            
            if result.get('status') == 'ok':
                # Save the template
                from report_genius.config import TEMPLATES_DIR
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
        
        This renders a template created by analyze_and_complete_template
        to a Word document with all Kahua placeholders properly formatted.
        
        Args:
            template_id: ID from analyze_and_complete_template
            output_name: Optional custom filename
            add_page_header: Include page header if not already present
            add_page_footer: Include page footer with page numbers
            
        Returns:
            Dict with download URL for the rendered document
        """
        try:
            import os
            from report_genius.config import TEMPLATES_DIR
            
            json_path = TEMPLATES_DIR / f"{template_id}.json"
            
            if not json_path.exists():
                return {"status": "error", "message": f"Template {template_id} not found"}
            
            template = PortableViewTemplate.model_validate_json(json_path.read_text())
            
            # Optionally add header/footer if not present
            if add_page_header and not template.layout.page_header:
                from report_genius.templates import PageHeaderFooterConfig
                template.layout.page_header = PageHeaderFooterConfig(
                    left_text=template.name,
                    font_size=10,
                )
            
            if add_page_footer and not template.layout.page_footer:
                from report_genius.templates import PageHeaderFooterConfig
                template.layout.page_footer = PageHeaderFooterConfig(
                    include_page_number=True,
                    page_number_format="Page {page} of {total}",
                    font_size=9,
                )
            
            # Render
            renderer = SOTADocxRenderer(template)
            doc_bytes = renderer.render_to_bytes()
            
            # Save
            reports_dir = Path(__file__).parent / "reports"
            reports_dir.mkdir(exist_ok=True)
            
            filename = output_name or template_id
            docx_path = reports_dir / f"{filename}.docx"
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
    
    agentic_template_tools = [
        analyze_and_complete_template,
        render_completed_template,
    ]
    log.info("Agentic template completion tools loaded")
except ImportError as e:
    agentic_template_tools = []
    log.warning(f"Agentic template tools not available: {e}")


# ============== Agent State ==============

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


# ============== LLM Setup ==============

def create_llm():
    """Create Claude LLM configured for Azure."""
    # Azure Anthropic endpoint format
    base_url = f"{AZURE_ENDPOINT}/anthropic"
    
    return ChatAnthropic(
        model=MODEL_DEPLOYMENT,
        api_key=AZURE_KEY,
        base_url=base_url,
        max_tokens=8192,
    )


# ============== System Prompt ==============

SYSTEM_PROMPT = """You are an expert Construction Project Analyst for Kahua. You create professional, data-driven reports and custom document templates. 

You are a helpful assistant that answers concisely and doesn't ramble/over-explain/add fluff. 

## CRITICAL: UPLOADED FILE DETECTION

╔════════════════════════════════════════════════════════════════════════════╗
║  IF USER MENTIONS AN UPLOADED FILE (.docx, .doc) OR SAYS "I UPLOADED":     ║
║                                                                            ║
║  WORKFLOW (Schema-Aware LLM Analysis):                                     ║
║  1. Call get_entity_fields(entity_type) to get REAL field paths            ║
║  2. Call analyze_template_with_llm(filename, entity_def) with schema       ║
║  3. Call inject_tokens_with_llm(filename, entity_def) to inject tokens     ║
║                                                                            ║
║  This approach:                                                            ║
║  - Uses ACTUAL field paths from Kahua schema (not guesses)                 ║
║  - Handles complex patterns (currency rows, checkboxes, inline blanks)     ║
║  - Preserves user's document layout completely                             ║
║                                                                            ║
║  NEVER generate a new template when user uploads one - PRESERVE their      ║
║  document layout and only inject tokens where blanks are detected.         ║
╚════════════════════════════════════════════════════════════════════════════╝

When a user uploads a designed template (with their logo, layout, styling):
1. Respect their design completely - do NOT regenerate
2. Determine the entity type (ask if unclear: "What entity type is this for?")
3. Fetch the schema first: get_entity_fields("change order") 
4. Then analyze and inject with full schema context

## TOOL SELECTION RULES

╔════════════════════════════════════════════════════════════════════════════╗
║  UPLOADED FILE:                                                            ║
║    get_entity_fields → analyze_template_with_llm → inject_tokens_with_llm  ║
║                                                                            ║
║  DISCOVER ENTITY TYPES:                                                    ║
║    list_supported_entities → shows all known entity types + aliases        ║
║                                                                            ║
║  EXPLORE FIELDS:                                                           ║
║    get_entity_fields("rfi") → shows all available fields with types        ║
║                                                                            ║
║  "CREATE/BUILD TEMPLATE" (no file) → build_custom_template → render        ║
║                                                                            ║
║  "REPORT" / "SHOW ME" / "LIST ALL" → query_entities → generate_report      ║
╚════════════════════════════════════════════════════════════════════════════╝

## SCHEMA SERVICE

Use get_entity_fields() and list_supported_entities() to understand what fields
are available before creating templates or analyzing documents. The schema service:
- Fetches REAL fields from Kahua API (not hardcoded guesses)
- Caches results for performance  
- Provides format hints (currency, date, boolean, etc.)
- Shows sample values to understand field content

Example: get_entity_fields("change order") returns:
- currency fields: OriginalContractAmount, CurrentContractAmount, etc.
- date fields: SubstantialCompletionDate, SubmittedDate, etc.
- boolean fields: IsContractSumIncreased, IsContractTimeDecreased, etc.

## WHAT IS A TEMPLATE?

A template is a **clean, production-ready document** with Kahua placeholders that will be 
filled with data when rendered in production. It should contain:
- Field placeholders like `[Attribute(RFI.Number)]`  
- Field labels and sections
- NO meta-text like "Template Specification" or "Design Guide"
- NO explanatory content about what the template is

## CUSTOM STYLING

When users request specific fonts, colors, or sizes, use the new parameters:

```
build_custom_template(
    entity_type="RFI",
    name="My Template",
    sections_json='[{"type": "detail", "fields": ["Number", "Subject"]}]',
    static_title="Beaus RFI Template",           # Literal text title
    title_style_json='{"font": "Comic Sans MS", "size": 28, "color": "#0000FF"}'
)
```

**static_title**: Literal text shown at top of document (NOT a placeholder)
**title_style_json**: JSON with font, size (points), color (hex), bold, alignment

## CORRECT EXAMPLES

### User: "Create an RFI template"
```
1. Call build_custom_template("RFI", "RFI View", '[{"type": "detail", "fields": ["Number", "Subject", "Status", "Priority", "Question", "Response"]}]')
2. Call render_smart_template(template_id)
3. Return download link
```
OUTPUT: Clean DOCX with `[Attribute(RFI.Number)]` placeholders - NO specification text.

### User: "Make an RFI template called 'Beaus RFI Template' in blue Comic Sans"
```
1. Call build_custom_template(
       "RFI", 
       "Beaus RFI Template",
       '[{"type": "detail", "fields": ["Number", "Subject", "Status"]}]',
       static_title="Beaus RFI Template",
       title_style_json='{"font": "Comic Sans MS", "size": 24, "color": "#0000FF"}'
   )
2. Call render_smart_template(template_id)
```
OUTPUT: DOCX with "Beaus RFI Template" in blue Comic Sans at top, then placeholders.

## WRONG EXAMPLES - NEVER DO THIS

❌ WRONG: generate_report(title="RFI Portable View Template Specification", markdown_content="...")
   This creates an analytics report document, NOT a template.

❌ WRONG: Outputting text that describes the template structure instead of building it.

❌ WRONG: Including text like "Template Design Guide" or "Specification" in the document.

## AVAILABLE ENTITIES

- RFI, Invoice, ExpenseContract, ExpenseChangeOrder, Submittal, FieldObservation

All are configured. When asked for a template, BUILD IT.

## WORKFLOW

1. User asks for template → Call build_custom_template with appropriate params
2. Get template_id from result
3. Call render_smart_template(template_id) to generate DOCX
4. Return download URL to user

## TOOLS SUMMARY

| Task                        | Tool                                           |
|-----------------------------|------------------------------------------------|
| Create template             | build_custom_template → render_smart_template  |
| Modify template             | modify_existing_template → render_smart_template|
| Create data report          | query_entities → generate_report               |
| Show entity fields          | get_entity_fields                              |
| List entities/counts        | count_entities, query_entities                 |

## Entity Aliases
- "rfi" → kahua_AEC_RFI.RFI
- "contract" → kahua_Contract.Contract  
- "invoice" → kahua_ContractInvoice.ContractInvoice
- "punch list" → kahua_AEC_PunchList.PunchListItem
- "submittal" → kahua_AEC_Submittal.Submittal
- "change order" → kahua_AEC_ChangeOrder.ChangeOrder

---

## KAHUA PLACEHOLDER SYNTAX REFERENCE

The DOCX renderer generates these placeholder formats automatically. This is what appears in the final document:

### Attribute (Text)
`[Attribute(RFI.Number)]` or `[Attribute(Parent.Child)]`

### Date
`[Date(Source=Attribute,Path=DueDate,Format="d")]`
- "D" = Long date, "d" = Short date

### Currency
`[Currency(Source=Attribute,Path=Amount,Format="C2")]`

### Number
`[Number(Source=Attribute,Path=Qty,Format="N0")]`
- "N0" = Integer, "F2" = 2 decimals, "P1" = Percent

### System
`[CompanyLogo(Height=60,Width=60)]`, `[ProjectName]`, `[ProjectNumber]`

### Tables
```
[StartTable(Name=Items,Source=Attribute,Path=LineItems,RowsInHeader=1)]
... row content with placeholders ...
[EndTable]
```

---

## EXAMPLE: WHAT A CORRECT TEMPLATE OUTPUT LOOKS LIKE

When you build an RFI template, the DOCX should contain content like:

```
[CompanyLogo(Height=60,Width=60)]

[Attribute(RFI.Number)]
[Attribute(RFI.Subject)]

Status: [Attribute(RFI.Status)]     Priority: [Attribute(RFI.Priority)]
Date: [Date(Source=Attribute,Path=RFI.Date,Format="d")]

Question
[Attribute(RFI.Question)]

Response  
[Attribute(RFI.Response)]
```

This is a CLEAN template. NO text like "Template Specification" or "Design Guide".
The placeholders ARE the content - Kahua fills them with real data.

---

## UPLOADED TEMPLATE ANALYSIS & TOKEN INJECTION

Users can upload existing Word templates that have "blank" placeholders like:
- "ID: " (label with trailing whitespace)
- "Status: ______" (label with underscores)
- "Date: [blank]" or "Date: <value>"
- Currency rows ending with "$" (e.g., "Original Contract Sum    $")
- Checkbox patterns (☐ increased ☐ decreased)
- Inline blanks like "(   ) days"

### LLM-DRIVEN INJECTION (PREFERRED - Use This!):

The LLM-driven analyzer is smarter and handles complex patterns that regex misses:

1. Call `analyze_template_with_llm(filename, entity_def)` to get intelligent analysis
   - Understands document context and semantics
   - Detects checkboxes, currency rows, inline blanks, conditional text
   - Maps fields based on surrounding context
2. Review the detected injection points with user
3. Call `inject_tokens_with_llm(filename, entity_def)` to inject all tokens
4. Return download link

Example:
User: "I uploaded a Change Order template, process it"
You: 
1. analyze_template_with_llm("change_order.docx", "kahua_AEC_ChangeOrder.ChangeOrder")
2. "I found 15 injection points including currency fields, checkboxes for increased/decreased, and contract time fields"
3. inject_tokens_with_llm("change_order.docx", "kahua_AEC_ChangeOrder.ChangeOrder")
4. Return download link

### AGENTIC TEMPLATE COMPLETION (For Modern Features):

For full template completion with modern features (page headers, footers, lists, etc.):

1. User uploads a .docx file via /upload endpoint
2. Call `analyze_and_complete_template(filename, entity_def, template_name)`
   - This analyzes the document's SEMANTIC STRUCTURE (sections, lists, tables)
   - Detects blanks AND document design intent
   - Creates a complete PortableViewTemplate with all features
3. Review the generated template structure with user
4. Call `render_completed_template(template_id)` to generate the final DOCX
5. Return download link

### Example Agentic Workflow:

User: "I uploaded my RFI template, complete it with Kahua tokens and add page numbers"

You:
1. Call analyze_and_complete_template("mytemplate.docx", "kahua_AEC_RFI.RFI", "My RFI Template")
2. Review: "I detected 3 sections with 8 fields. Created template pv-abc123 with:
   - Header section with title
   - Detail section with RFI fields
   - List section with action items
   - Page footer with page numbers"
3. Call render_completed_template("pv-abc123")
4. Return: "Here's your completed template with all features: [download link]"

This approach creates PROFESSIONAL templates with:
- Page headers/footers with page numbers
- Bullet/numbered lists with field placeholders
- Properly structured sections
- Kahua token syntax throughout

### Token Mapping Guide

Use `show_token_mapping_guide()` to see how labels like "ID:" map to Kahua paths.
Common mappings:
- ID/Number/Ref → Number
- Status/State → Status.Name  
- Due/Due Date → DueDate
- From/Submitted By → SubmittedBy.Name

---

## OUTPUT FORMAT
- Use markdown tables for field lists
- Bold important values
- Status icons where appropriate
- Keep responses concise
"""


# ============== Schema Service Tools ==============

try:
    from src.report_genius.schema_service import (
        get_schema_service,
        get_entity_schema as fetch_entity_schema,
        resolve_entity,
        get_display_name,
    )
    
    @tool
    async def get_entity_fields(entity_name: str) -> dict:
        """
        Get all fields available for an entity type.
        
        Use this tool to understand what fields can be used in templates.
        Returns field paths, types, format hints (currency, date, etc.).
        
        Args:
            entity_name: Entity type - can be natural language (e.g., "change order") 
                        or full definition (e.g., "kahua_AEC_ChangeOrder.ChangeOrder")
        
        Returns:
            Dict with entity_def, display_name, and fields organized by format type
        """
        try:
            schema = await fetch_entity_schema(entity_name)
            if not schema:
                return {"error": f"Could not fetch schema for '{entity_name}'"}
            
            # Organize fields by format
            by_format = {}
            for f in schema.fields:
                by_format.setdefault(f.format_hint, []).append({
                    "path": f.path,
                    "label": f.label,
                    "sample": f.sample_value,
                })
            
            return {
                "entity_def": schema.entity_def,
                "display_name": schema.display_name,
                "field_count": len(schema.fields),
                "fields_by_type": by_format,
                "child_collections": schema.child_collections,
            }
        except Exception as e:
            return {"error": str(e)}
    
    @tool
    def list_supported_entities() -> dict:
        """
        List all known entity types and their aliases.
        
        Use this tool to discover what entity types the user might be
        referring to (e.g., "change order", "rfi", "submittal").
        
        Returns:
            List of entity definitions with display names and aliases
        """
        service = get_schema_service()
        return {
            "entities": service.list_known_entities()
        }
    
    schema_tools = [get_entity_fields, list_supported_entities]
    log.info("Schema service tools loaded")
except ImportError as e:
    schema_tools = []
    log.warning(f"Schema service tools not available: {e}")


# ============== Graph Definition ==============

def create_agent():
    """Create the LangGraph agent."""
    
    # All tools - include unified SOTA tools, DOCX injection, LLM injection, schema tools, and agentic completion
    # Note: get_entity_schema replaced by get_entity_fields from schema service (more comprehensive)
    all_tools = [find_project, count_entities, query_entities, generate_report] + pv_tools + template_gen_tools + unified_template_tools + docx_injection_tools + llm_injection_tools + schema_tools + agentic_template_tools
    
    # Create LLM with tools bound
    llm = create_llm()
    llm_with_tools = llm.bind_tools(all_tools)
    
    # Max messages to keep in context (prevent token overflow)
    MAX_MESSAGES = 30  # Keep recent conversation manageable
    
    # Agent node - calls LLM
    def agent_node(state: AgentState):
        messages = state["messages"]
        
        # Ensure system message is first
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
        
        # Truncate message history if too long (keep system + recent messages)
        if len(messages) > MAX_MESSAGES:
            system_msg = messages[0] if isinstance(messages[0], SystemMessage) else None
            recent_messages = messages[-(MAX_MESSAGES - 1):] if system_msg else messages[-MAX_MESSAGES:]
            if system_msg:
                messages = [system_msg] + recent_messages
            else:
                messages = recent_messages
            log.info(f"Truncated message history to {len(messages)} messages")
        
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}
    
    # Tool node - executes tools
    tool_node = ToolNode(all_tools)
    
    # Router - decide next step
    def should_continue(state: AgentState):
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return END
    
    # Build graph
    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)
    
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")
    
    # Compile with memory
    memory = MemorySaver()
    return graph.compile(checkpointer=memory)


# ============== Main Interface ==============

_agent = None

def get_agent():
    """Get or create the agent singleton."""
    global _agent
    if _agent is None:
        log.info(f"Creating LangGraph agent with model: {MODEL_DEPLOYMENT}")
        _agent = create_agent()
    return _agent


# Session storage for recovery
_session_checkpointers: Dict[str, MemorySaver] = {}


def _detect_recent_uploads() -> List[str]:
    """Check for recently uploaded .docx files (within last 5 minutes)."""
    import time
    uploads_dir = Path(__file__).parent / "uploads"
    if not uploads_dir.exists():
        return []
    
    recent = []
    now = time.time()
    for f in uploads_dir.glob("*.docx"):
        # Skip already-processed files
        if f.name.startswith(("tokenized_", "original_")):
            continue
        # Check if modified recently (within 5 minutes)
        if now - f.stat().st_mtime < 300:
            recent.append(f.name)
    return recent


def _augment_message_with_upload_context(message: str) -> str:
    """
    If there are recent uploads and the message seems template-related,
    add context to guide the agent to use the injection workflow.
    """
    recent = _detect_recent_uploads()
    if not recent:
        return message
    
    # Check if message might be about processing a template
    template_keywords = ['template', 'process', 'inject', 'token', 'fill', 'complete', 
                         'uploaded', 'file', 'docx', 'change order', 'rfi', 'invoice']
    msg_lower = message.lower()
    
    if any(kw in msg_lower for kw in template_keywords):
        # Add context about the uploaded file
        files_str = ", ".join(recent)
        context = f"\n\n[SYSTEM NOTE: Recent uploads detected in uploads/ folder: {files_str}. " \
                  f"If user wants to process these, use analyze_uploaded_template → inject_tokens_into_template " \
                  f"to PRESERVE their layout, not build_custom_template.]"
        return message + context
    
    return message


def reset_session(session_id: str = "default") -> bool:
    """
    Reset a corrupted session to allow fresh conversation.
    Call this if a session gets into a bad state with pending tool calls.
    
    Returns True if session was reset.
    """
    global _agent
    # Easiest way is to clear and recreate the agent with fresh memory
    _agent = None
    log.info(f"Session {session_id} reset - agent will be recreated")
    return True


async def chat(message: str, session_id: str = "default") -> str:
    """
    Send a message to the agent and get a response.
    
    Args:
        message: User message
        session_id: Session ID for conversation memory
    
    Returns:
        Agent response text
    """
    agent = get_agent()
    
    # Augment with upload context if relevant
    augmented_message = _augment_message_with_upload_context(message)
    
    config = {"configurable": {"thread_id": session_id}}
    
    try:
        result = await agent.ainvoke(
            {"messages": [HumanMessage(content=augmented_message)]},
            config=config
        )
        
        # Get the last AI message
        for msg in reversed(result["messages"]):
            if isinstance(msg, AIMessage):
                return msg.content
        
        return "No response generated."
    except Exception as e:
        error_str = str(e)
        # Check for the specific tool_use/tool_result mismatch error
        if "tool_use ids were found without tool_result" in error_str:
            log.warning(f"Session {session_id} corrupted (pending tool calls), resetting...")
            reset_session(session_id)
            # Retry with fresh agent
            agent = get_agent()
            result = await agent.ainvoke(
                {"messages": [HumanMessage(content=message)]},
                config=config
            )
            for msg in reversed(result["messages"]):
                if isinstance(msg, AIMessage):
                    return msg.content
            return "No response generated."
        else:
            raise


def chat_sync(message: str, session_id: str = "default") -> str:
    """Synchronous version of chat."""
    agent = get_agent()
    
    # Augment with upload context if relevant
    augmented_message = _augment_message_with_upload_context(message)
    
    config = {"configurable": {"thread_id": session_id}}
    
    try:
        result = agent.invoke(
            {"messages": [HumanMessage(content=augmented_message)]},
            config=config
        )
        
        for msg in reversed(result["messages"]):
            if isinstance(msg, AIMessage):
                return msg.content
        
        return "No response generated."
    except Exception as e:
        error_str = str(e)
        if "tool_use ids were found without tool_result" in error_str:
            log.warning(f"Session {session_id} corrupted, resetting...")
            reset_session(session_id)
            agent = get_agent()
            result = agent.invoke(
                {"messages": [HumanMessage(content=message)]},
                config=config
            )
            for msg in reversed(result["messages"]):
                if isinstance(msg, AIMessage):
                    return msg.content
            return "No response generated."
        else:
            raise


# ============== Test ==============

if __name__ == "__main__":
    print("Testing LangGraph agent...")
    response = chat_sync("Hello! What model are you?")
    print(f"\nResponse:\n{response}")
