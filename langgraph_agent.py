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
    Generate a professional Word document report.
    
    Args:
        title: Report title.
        markdown_content: Body content in markdown format.
        subtitle: Optional subtitle.
        charts_json: JSON array of chart specs.
    
    Returns:
        Dict with filename and download URL.
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
            from pathlib import Path
            output_dir = Path(__file__).parent / "pv_templates" / "saved"
            output_dir.mkdir(parents=True, exist_ok=True)
            json_path = output_dir / f"{template.id}.json"
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
            from template_gen.template_schema import PortableViewTemplate
            
            # Find template
            saved_dir = Path(__file__).parent / "pv_templates" / "saved"
            json_path = saved_dir / f"{template_id}.json"
            
            if not json_path.exists():
                return {"status": "error", "message": f"Template {template_id} not found"}
            
            # Load and render
            template = PortableViewTemplate.model_validate_json(json_path.read_text())
            system = get_unified_system()
            
            reports_dir = Path(__file__).parent / "reports"
            reports_dir.mkdir(exist_ok=True)
            
            filename = output_name or template_id
            docx_path = reports_dir / f"{filename}.docx"
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
        
        Example:
            User: "I want a template for RFIs"
            -> Call get_entity_fields("RFI")
            -> Show user the fields
            -> Ask: "Which of these fields would you like included?"
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
        layout: str = "single_column"
    ) -> dict:
        """
        Build a template with EXACT fields and styling specified by the user.
        
        Use this after asking the user what they want. Build the template
        based on their specific instructions, not from archetypes.
        
        Args:
            entity_type: Entity type (e.g., "Invoice", "RFI")
            name: Template name chosen by user
            sections_json: JSON array of section specs. Each section:
                {
                    "type": "header" | "detail" | "table" | "text",
                    "title": "Section Title" (optional),
                    "fields": ["FieldPath1", "FieldPath2", ...],
                    "formatting": {
                        "bold_fields": ["FieldPath1"],  // Fields to bold
                        "columns": 2,  // For detail sections
                    }
                }
            include_logo: Whether to include company logo placeholder
            layout: "single_column" or "two_column"
        
        Returns:
            Dict with template_id and structure summary
        
        Example usage:
            User says: "I want Subject and Description in bold, two columns"
            -> build_custom_template("RFI", "My RFI View", 
                '[{"type": "detail", "fields": ["Subject", "Description"], 
                  "formatting": {"bold_fields": ["Subject", "Description"], "columns": 2}}]')
        """
        try:
            import json as json_module
            import uuid
            from template_gen.template_schema import (
                PortableViewTemplate, Section, SectionType,
                HeaderConfig, DetailConfig, TableConfig, TextConfig,
                FieldDef, FieldFormat as TGFieldFormat, TableColumn,
                LayoutConfig,
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
            for idx, spec in enumerate(sections_spec):
                sec_type = SectionType(spec.get("type", "detail"))
                title = spec.get("title", "")
                fields = spec.get("fields", [])
                formatting = spec.get("formatting", {})
                
                if sec_type == SectionType.HEADER:
                    # Header section
                    field_defs = [resolve_field(f) for f in fields]
                    title_field = field_defs[0] if field_defs else None
                    config = HeaderConfig(
                        title_template=f"{{{title_field.path}}}" if title_field else "{Number}",
                        subtitle_template=f"{{{field_defs[1].path}}}" if len(field_defs) > 1 else None,
                        fields=field_defs[2:] if len(field_defs) > 2 else [],
                        show_logo=include_logo,
                    )
                    built_sections.append(Section(
                        type=SectionType.HEADER, order=idx, header_config=config
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
                        type=SectionType.DETAIL, title=title, order=idx, detail_config=config
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
                        type=SectionType.TABLE, title=title, order=idx, table_config=config
                    ))
                    
                elif sec_type == SectionType.TEXT:
                    # Text/content section
                    content = spec.get("content", "")
                    if not content and fields:
                        # Use fields as content blocks
                        content = "\n\n".join(f"{{{f}}}" for f in fields)
                    config = TextConfig(content=content)
                    built_sections.append(Section(
                        type=SectionType.TEXT, title=title, order=idx, text_config=config
                    ))
            
            # Create template
            template_id = f"pv-{uuid.uuid4().hex[:8]}"
            template = PortableViewTemplate(
                id=template_id,
                name=name,
                entity_def=schema.entity_def,
                version="1.0",
                sections=built_sections,
                layout=LayoutConfig(columns=2 if layout == "two_column" else 1),
            )
            
            # Save to disk and active templates
            from pathlib import Path
            output_dir = Path(__file__).parent / "pv_templates" / "saved"
            output_dir.mkdir(parents=True, exist_ok=True)
            json_path = output_dir / f"{template_id}.json"
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
            from template_gen.template_schema import (
                PortableViewTemplate, Section, SectionType,
                HeaderConfig, DetailConfig, FieldDef, FieldFormat as TGFieldFormat,
            )
            
            # Load template
            saved_dir = Path(__file__).parent / "pv_templates" / "saved"
            json_path = saved_dir / f"{template_id}.json"
            
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
            from pathlib import Path
            from template_gen.template_schema import PortableViewTemplate
            
            saved_dir = Path(__file__).parent / "pv_templates" / "saved"
            json_path = saved_dir / f"{template_id}.json"
            
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
        get_entity_fields,
        build_custom_template,
        modify_existing_template,
        preview_template_structure,
    ]
    log.info("Unified SOTA template tools loaded (including interactive tools)")
except ImportError as e:
    unified_template_tools = []
    log.warning(f"Unified template tools not available: {e}")


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

## CORE PRINCIPLE: USE YOUR TOOLS

You have tools that work. When a user asks for something, USE THE TOOLS - don't guess whether they'll work.

**AVAILABLE ENTITY TYPES FOR TEMPLATES:**
- RFI (Request for Information)
- Invoice
- ExpenseContract
- ExpenseChangeOrder
- Submittal
- FieldObservation

These entities are CONFIGURED and READY. When a user asks for a template for any of these, BUILD IT using `build_custom_template`.

## WHAT YOU CAN DO

- Query Kahua entities (RFIs, contracts, submittals, etc.)
- Generate Word document templates with Kahua placeholder syntax
- Create CUSTOM templates based on user specifications using `build_custom_template`
- Modify templates based on user feedback using `modify_existing_template`
- Create reports from queried data

## WHAT YOU CANNOT DO

- Add actual images/photos to documents (but CAN add logo placeholders)
- Modify Kahua system settings

## TEMPLATE CREATION WORKFLOW

When a user asks for a template, portable view, or document design:

### STEP 1: If they specify what they want, BUILD IT IMMEDIATELY
If the user gives you fields and formatting preferences, call `build_custom_template` right away.

Example:
User: "Build me an RFI template with Number, Subject, Question, Response. Two columns, make Subject bold."
→ IMMEDIATELY call build_custom_template("RFI", "RFI Portable View", sections_json, layout="two_column")

### STEP 2: If they're vague, show available fields first
Call `get_entity_fields(entity_type)` to show what's available.

Example:
User: "I need a portable view for RFIs"
→ Call get_entity_fields("RFI") and show the fields
→ Ask: "Which fields would you like included?"

### STEP 3: Handle modifications
When they ask for changes, use `modify_existing_template`:
- "remove the logo" → modify_existing_template(id, "toggle_logo", '{"show": false}')
- "make Subject bold" → modify_existing_template(id, "set_bold", '{"fields": ["Subject"]}')

### STEP 4: Render when ready
Call `render_smart_template(template_id)` to generate the DOCX.

## EXAMPLE - ONE-SHOT TEMPLATE CREATION

User: "Build me an RFI template with Number, Subject, Question, Response. Two columns, make Subject bold."

You: [Call build_custom_template immediately]
```
build_custom_template(
    entity_type="RFI",
    name="RFI Portable View",
    sections_json='[{"type": "header", "fields": ["Number", "Subject"]}, {"type": "detail", "fields": ["Question", "Response"], "formatting": {"bold_fields": ["Subject"], "columns": 2}}]',
    layout="two_column"
)
```

Response: "✅ Created your RFI template (pv-abc123):
- Header: Number, Subject  
- Detail: Question, Response (2 columns)
- Subject in bold

**Download:** [RFI_Portable_View.docx](/reports/pv-abc123.docx)

Want any changes?"

## TOOLS REFERENCE

### Interactive Template Building (PREFERRED)
- **get_entity_fields(entity_type)**: Show user what fields are available
- **build_custom_template(...)**: Build template with user-specified fields and formatting
- **modify_existing_template(template_id, operation, config_json)**: Change templates based on feedback
- **preview_template_structure(template_id)**: Show current template structure
- **render_smart_template(template_id)**: Generate the final DOCX

### Quick Template (when user wants something fast)
- **smart_compose_template(entity_type, archetype, user_intent)**: Auto-generate with archetype
- **list_template_archetypes()**: See available design patterns

### Data Access
- **find_project(search_term)**: Find project by name
- **count_entities(entity_def)**: Count records
- **query_entities(entity_def, ...)**: Get entity data
- **get_entity_schema(entity_def)**: See entity fields from live data
- **generate_report(title, markdown_content)**: Create Word reports

## Entity Aliases
- "rfi" → kahua_AEC_RFI.RFI
- "contract" → kahua_Contract.Contract  
- "invoice" → kahua_ContractInvoice.ContractInvoice
- "punch list" → kahua_AEC_PunchList.PunchListItem
- "submittal" → kahua_AEC_Submittal.Submittal
- "change order" → kahua_AEC_ChangeOrder.ChangeOrder

## OUTPUT FORMAT
- Use markdown tables for field lists
- Bold important values
- Status icons where appropriate: ✅ ⚠️ ❌
- Keep responses concise
"""


# ============== Graph Definition ==============

def create_agent():
    """Create the LangGraph agent."""
    
    # All tools - include unified SOTA tools
    all_tools = [find_project, count_entities, query_entities, get_entity_schema, generate_report] + pv_tools + template_gen_tools + unified_template_tools
    
    # Create LLM with tools bound
    llm = create_llm()
    llm_with_tools = llm.bind_tools(all_tools)
    
    # Agent node - calls LLM
    def agent_node(state: AgentState):
        messages = state["messages"]
        
        # Ensure system message is first
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
        
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
    
    config = {"configurable": {"thread_id": session_id}}
    
    result = await agent.ainvoke(
        {"messages": [HumanMessage(content=message)]},
        config=config
    )
    
    # Get the last AI message
    for msg in reversed(result["messages"]):
        if isinstance(msg, AIMessage):
            return msg.content
    
    return "No response generated."


def chat_sync(message: str, session_id: str = "default") -> str:
    """Synchronous version of chat."""
    agent = get_agent()
    
    config = {"configurable": {"thread_id": session_id}}
    
    result = agent.invoke(
        {"messages": [HumanMessage(content=message)]},
        config=config
    )
    
    for msg in reversed(result["messages"]):
        if isinstance(msg, AIMessage):
            return msg.content
    
    return "No response generated."


# ============== Test ==============

if __name__ == "__main__":
    print("Testing LangGraph agent...")
    response = chat_sync("Hello! What model are you?")
    print(f"\nResponse:\n{response}")
