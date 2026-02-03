"""
Template Builder API Routes

Backend API endpoints for the visual template builder.
"""

import os
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

# Template infrastructure - uses OLD dataclass schema (for .from_dict/.to_dict compatibility)
# TODO: Migrate to new Pydantic schema once endpoints are updated
from pv_template_schema import (
    PortableTemplate,
    Section,
    SectionType,
    FieldMapping,
    FieldFormat,
    HeaderSection,
    DetailSection,
    TableSection,
    TextSection,
    ColumnDef,
    Alignment,
    PageLayout,
    StyleConfig,
)
from pv_template_analyzer import analyze_document_description, refine_template
from pv_template_renderer import TemplateRenderer

log = logging.getLogger("template_builder_api")

router = APIRouter(prefix="/api/template", tags=["Template Builder"])

# Storage paths - use canonical config
from report_genius.config import TEMPLATES_DIR as PV_TEMPLATES_DIR

# ============== Kahua API Config ==============

QUERY_URL_TEMPLATE = "https://demo01service.kahua.com/v2/domains/Summit/projects/{project_id}/query?returnDefaultAttributes=true"
KAHUA_BASIC_AUTH = os.getenv("KAHUA_BASIC_AUTH")

def _auth_header_value() -> str:
    if not KAHUA_BASIC_AUTH:
        raise RuntimeError("KAHUA_BASIC_AUTH not set")
    return KAHUA_BASIC_AUTH if KAHUA_BASIC_AUTH.strip().lower().startswith("basic ") \
           else f"Basic {KAHUA_BASIC_AUTH}"

HEADERS_JSON = lambda: {"Content-Type": "application/json", "Authorization": _auth_header_value()}


# ============== Request/Response Models ==============

class SaveTemplateRequest(BaseModel):
    """Request to save a template."""
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    target_entity_def: str
    target_entity_aliases: List[str] = []
    layout: Dict[str, Any]
    style: Dict[str, Any]
    sections: List[Dict[str, Any]]
    category: str = "custom"
    tags: List[str] = []
    is_public: bool = False


class AIAssistRequest(BaseModel):
    """Request for AI-assisted template modification."""
    instruction: str
    current_template: Dict[str, Any]
    entity_schema: Optional[Dict[str, Any]] = None


class RenderPreviewRequest(BaseModel):
    """Request to render a preview document."""
    template: Dict[str, Any]
    data: Dict[str, Any]


# ============== Entity Schema via Kahua API ==============

# Entity display name mappings
ENTITY_DISPLAY_NAMES = {
    "kahua_Contract.Contract": "Contract",
    "kahua_AEC_RFI.RFI": "RFI",
    "kahua_AEC_Submittal.Submittal": "Submittal",
    "kahua_AEC_ChangeOrder.ChangeOrder": "Change Order",
    "kahua_AEC_PunchList.PunchListItem": "Punch List Item",
    "kahua_AEC_DailyReport.DailyReport": "Daily Report",
    "kahua_Meeting.Meeting": "Meeting",
    "kahua_Project.Project": "Project",
    "kahua_ContractInvoice.ContractInvoice": "Invoice",
    "kahua_ContractChangeRequest.ContractChangeRequest": "Change Request",
}

# Known child entity paths for common entities
CHILD_ENTITY_PATHS = {
    "kahua_Contract.Contract": [
        {"path": "Items", "entity_def": "kahua_Contract.ContractItem", "display_name": "Contract Items"},
    ],
    "kahua_AEC_ChangeOrder.ChangeOrder": [
        {"path": "Items", "entity_def": "kahua_AEC_ChangeOrder.ChangeOrderItem", "display_name": "Change Order Items"},
    ],
}


def _infer_format_from_value(key: str, value: Any) -> str:
    """Infer the field format from the key name and sample value."""
    key_lower = key.lower()
    
    # Check by key name patterns
    if any(x in key_lower for x in ['amount', 'cost', 'price', 'value', 'total', 'fee', 'budget']):
        return 'currency'
    if any(x in key_lower for x in ['percent', 'percentage', 'pct', 'rate']):
        return 'percentage'
    if key_lower in ['date', 'duedate', 'startdate', 'enddate'] or key_lower.endswith('date'):
        return 'date'
    if 'datetime' in key_lower or key_lower in ['created', 'modified', 'createddatetime', 'modifieddatetime']:
        return 'datetime'
    if any(x in key_lower for x in ['count', 'number', 'qty', 'quantity', 'days', 'hours']):
        if not key_lower == 'number':  # 'Number' is usually an ID/label
            return 'number'
    if any(x in key_lower for x in ['notes', 'description', 'comment', 'body', 'text', 'content', 'question', 'answer', 'scope']):
        return 'rich_text'
    if any(x in key_lower for x in ['email', 'mail']):
        return 'email'
    if any(x in key_lower for x in ['phone', 'tel', 'fax', 'mobile']):
        return 'phone'
    
    # Check by value type
    if value is None:
        return 'text'
    if isinstance(value, bool):
        return 'boolean'
    if isinstance(value, float):
        return 'number'
    if isinstance(value, int):
        return 'number'
    if isinstance(value, dict):
        return 'text'  # Reference field
    if isinstance(value, list):
        return 'text'
    if isinstance(value, str):
        # Check if it looks like a date
        if 'T' in value and len(value) > 15:
            return 'datetime'
    
    return 'text'


def _make_label(key: str) -> str:
    """Convert a camelCase or PascalCase key to a human-readable label."""
    import re
    # Insert space before uppercase letters
    result = re.sub(r'([a-z])([A-Z])', r'\1 \2', key)
    # Handle consecutive uppercase (like 'RFI' -> 'RFI')
    result = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1 \2', result)
    return result


def _extract_attributes_from_sample(sample: Dict[str, Any], prefix: str = "", depth: int = 0) -> List[Dict[str, Any]]:
    """Extract attribute definitions from a sample entity record - ALL fields."""
    attributes = []
    
    # Skip these internal/system fields only at top level
    skip_fields = {'_links', '_embedded', 'Links', 'Embedded', 'EntityDef', 
                   'PartitionScope', 'IsLegacy', 'Hash', 'Marker', 
                   'RowVersion', 'RecordId', 'UniqueId', 'hubPath'}
    
    # Max recursion depth for nested objects
    if depth > 2:
        return attributes
    
    for key, value in sample.items():
        if key in skip_fields and depth == 0:
            continue
        if key.startswith('_'):
            continue
            
        full_path = f"{prefix}{key}" if prefix else key
        
        # Handle nested objects (reference fields)
        if isinstance(value, dict) and value:
            # Always add common display fields from nested objects
            display_fields = ['ShortLabel', 'Name', 'Number', 'Label', 'DisplayName', 'Title']
            added_display = False
            
            for display_field in display_fields:
                if display_field in value:
                    attributes.append({
                        "path": f"{full_path}.{display_field}",
                        "name": key,
                        "label": _make_label(key),
                        "type": "reference",
                        "format": "text"
                    })
                    added_display = True
                    break
            
            # If no display field found, recurse into the object
            if not added_display and depth < 2:
                nested_attrs = _extract_attributes_from_sample(value, f"{full_path}.", depth + 1)
                attributes.extend(nested_attrs)
            
            # Also add ID if available
            if 'Id' in value:
                attributes.append({
                    "path": f"{full_path}.Id",
                    "name": f"{key}Id",
                    "label": f"{_make_label(key)} ID",
                    "type": "integer",
                    "format": "number"
                })
                
        elif isinstance(value, list):
            # For list fields, note them but don't recurse (child collections)
            if value and isinstance(value[0], dict):
                # This is a child collection - skip for main attributes
                continue
            else:
                # Simple list (e.g., tags, ids)
                attributes.append({
                    "path": full_path,
                    "name": key,
                    "label": _make_label(key),
                    "type": "list",
                    "format": "text"
                })
        else:
            # Simple field - always include
            format_type = _infer_format_from_value(key, value)
            attributes.append({
                "path": full_path,
                "name": key,
                "label": _make_label(key),
                "type": type(value).__name__ if value is not None else "string",
                "format": format_type
            })
    
    return sorted(attributes, key=lambda x: x["path"])


async def _query_entity_samples(entity_def: str, count: int = 10, project_id: int = 0) -> List[Dict[str, Any]]:
    """Query Kahua for multiple sample entity records to get complete field coverage."""
    query_url = QUERY_URL_TEMPLATE.format(project_id=project_id)
    qpayload = {
        "PropertyName": "Query", 
        "EntityDef": entity_def, 
        "Take": str(count),
        "Partition": {"Scope": "Any"}
    }
    
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(query_url, headers=HEADERS_JSON(), json=qpayload)
            if resp.status_code >= 400:
                log.warning(f"Failed to query {entity_def}: {resp.status_code}")
                return []
            body = resp.json()
        
        # Find all records
        samples = []
        for key in ("entities", "results", "items"):
            if isinstance(body.get(key), list) and body[key]:
                samples = body[key]
                break
        for s in body.get("sets", []):
            if isinstance(s.get("entities"), list) and s["entities"]:
                samples = s["entities"]
                break
        
        return samples
    except Exception as e:
        log.error(f"Error querying {entity_def}: {e}")
        return []


def _merge_samples_to_schema(samples: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Merge multiple sample records to get complete field coverage.
    
    Handles the Kahua v2 API format where attributes are flat top-level keys.
    """
    merged = {}
    
    for sample in samples:
        for key, value in sample.items():
            if key not in merged:
                merged[key] = value
            elif merged[key] is None and value is not None:
                # Prefer non-null values
                merged[key] = value
            elif isinstance(merged[key], dict) and isinstance(value, dict):
                # Merge nested dicts to get more fields
                for nested_key, nested_val in value.items():
                    if nested_key not in merged[key]:
                        merged[key][nested_key] = nested_val
                    elif merged[key][nested_key] is None and nested_val is not None:
                        merged[key][nested_key] = nested_val
    
    return merged


def _extract_attributes_from_merged(merged: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract attribute definitions from merged sample data (v1 API format)."""
    attributes = []
    
    # Extract from attributes dict
    for name, value in merged.get("attributes", {}).items():
        if name.startswith("_") or name in {"EntityDef", "PartitionScope", "IsLegacy", "Hash", "Marker", "RowVersion", "RecordId", "UniqueId", "hubPath"}:
            continue
        
        format_type = _infer_format_from_value(name, value)
        attributes.append({
            "path": name,
            "name": name,
            "label": _make_label(name),
            "type": type(value).__name__ if value is not None else "string",
            "format": format_type
        })
    
    # Extract from outward references
    for name, ref in merged.get("outwardReferences", {}).items():
        # Add the reference as a field
        attributes.append({
            "path": f"{name}.Name",
            "name": name,
            "label": _make_label(name),
            "type": "reference",
            "format": "text"
        })
        # Also add the ID
        attributes.append({
            "path": f"{name}.Id",
            "name": f"{name}Id",
            "label": f"{_make_label(name)} ID",
            "type": "integer",
            "format": "number"
        })
    
    return sorted(attributes, key=lambda x: x["path"])


@router.get("/schema/{entity_def:path}")
async def get_entity_schema(entity_def: str) -> Dict[str, Any]:
    """Get the schema for an entity type by querying multiple Kahua records."""
    # Decode URL encoding
    entity_def = entity_def.replace("%2E", ".")
    
    # Get display name
    display_name = ENTITY_DISPLAY_NAMES.get(entity_def, entity_def.split(".")[-1])
    
    # Query Kahua for multiple sample records to get complete field coverage
    samples = await _query_entity_samples(entity_def, count=15)
    
    if not samples:
        log.warning(f"No samples found for {entity_def}, returning minimal schema")
        return {
            "entity_def": entity_def,
            "display_name": display_name,
            "description": f"No records found for {entity_def}",
            "attributes": [
                {"path": "Number", "name": "Number", "label": "Number", "type": "string", "format": "text"},
                {"path": "Description", "name": "Description", "label": "Description", "type": "string", "format": "text"},
            ],
            "child_entities": []
        }
    
    # Merge all samples to get complete field coverage
    merged_sample = _merge_samples_to_schema(samples)
    
    # Extract attributes from the merged sample (v2 API flat format)
    attributes = _extract_attributes_from_sample(merged_sample)
    
    # Get child entities
    child_entities = []
    for child_def in CHILD_ENTITY_PATHS.get(entity_def, []):
        child_samples = await _query_entity_samples(child_def["entity_def"], count=10)
        if child_samples:
            merged_child = _merge_samples_to_schema(child_samples)
            child_attrs = _extract_attributes_from_sample(merged_child)
            child_entities.append({
                "path": child_def["path"],
                "entity_def": child_def["entity_def"],
                "display_name": child_def["display_name"],
                "attributes": child_attrs
            })
        else:
            child_entities.append({
                "path": child_def["path"],
                "entity_def": child_def["entity_def"],
                "display_name": child_def["display_name"],
                "attributes": []
            })
    
    log.info(f"Loaded schema for {entity_def}: {len(attributes)} attributes from {len(samples)} samples, {len(child_entities)} children")
    
    
    return {
        "entity_def": entity_def,
        "display_name": display_name,
        "description": f"Schema for {display_name}",
        "attributes": attributes,
        "child_entities": child_entities
    }


@router.get("/entities")
async def list_available_entities() -> List[Dict[str, str]]:
    """List available entity types for template creation."""
    return [
        {"entity_def": k, "display_name": v}
        for k, v in ENTITY_DISPLAY_NAMES.items()
    ]


# ============== Template CRUD ==============

@router.post("/save")
async def save_template(req: SaveTemplateRequest) -> Dict[str, Any]:
    """Save a portable view template."""
    import uuid
    from datetime import datetime
    
    # Generate ID if new
    template_id = req.id or f"pv-{uuid.uuid4().hex[:8]}"
    
    # Build template dict
    template_data = {
        "id": template_id,
        "name": req.name,
        "description": req.description,
        "version": "1.0",
        "target_entity_def": req.target_entity_def,
        "target_entity_aliases": req.target_entity_aliases,
        "layout": req.layout,
        "style": req.style,
        "sections": req.sections,
        "category": req.category,
        "tags": req.tags,
        "is_public": req.is_public,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }
    
    # If updating, preserve created_at
    file_path = PV_TEMPLATES_DIR / f"{template_id}.json"
    if file_path.exists():
        try:
            with open(file_path, 'r') as f:
                existing = json.load(f)
                template_data["created_at"] = existing.get("created_at", template_data["created_at"])
        except Exception:
            pass
    
    # Save
    with open(file_path, 'w') as f:
        json.dump(template_data, f, indent=2)
    
    log.info(f"Saved template: {template_id}")
    
    return {
        "status": "ok",
        "id": template_id,
        "message": f"Template '{req.name}' saved successfully"
    }


@router.delete("/{template_id}")
async def delete_template(template_id: str) -> Dict[str, Any]:
    """Delete a template."""
    if ".." in template_id or "/" in template_id or "\\" in template_id:
        raise HTTPException(status_code=400, detail="Invalid template ID")
    
    file_path = PV_TEMPLATES_DIR / f"{template_id}.json"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Template not found")
    
    file_path.unlink()
    log.info(f"Deleted template: {template_id}")
    
    return {"status": "ok", "message": f"Template {template_id} deleted"}


# ============== AI Assistance ==============

@router.post("/ai-assist")
async def ai_assist(req: AIAssistRequest) -> Dict[str, Any]:
    """Process an AI assistance request to modify the template."""
    try:
        log.info(f"AI assist request: {req.instruction[:100]}...")
        
        # Convert current template dict to PortableTemplate
        try:
            current = PortableTemplate.from_dict(req.current_template)
            log.info(f"Template converted: {current.name}, {len(current.sections)} sections")
        except Exception as e:
            log.error(f"Failed to parse template: {e}")
            raise ValueError(f"Invalid template format: {e}")
        
        # Get available fields from schema
        available_fields = []
        if req.entity_schema:
            available_fields = req.entity_schema.get("attributes", [])
            log.info(f"Schema has {len(available_fields)} attributes")
        
        # Use the refine_template function
        try:
            modified, changes = await refine_template(
                template=current,
                instruction=req.instruction,
                available_fields=available_fields
            )
            log.info(f"Refinement complete: {changes}")
        except Exception as e:
            log.error(f"refine_template failed: {e}", exc_info=True)
            raise ValueError(f"AI processing failed: {e}")
        
        return {
            "status": "ok",
            "template": modified.to_dict(),
            "message": f"Applied changes: {', '.join(changes) if changes else 'Template updated'}",
            "changes": changes,
            "suggestions": [
                "Add more fields to capture additional data",
                "Consider adding a summary section",
                "Add conditional visibility for optional fields"
            ]
        }
    except Exception as e:
        log.error(f"AI assist error: {e}", exc_info=True)
        # Return error as JSON, not 500
        return {
            "status": "error",
            "message": str(e),
            "template": req.current_template  # Return unchanged
        }


# ============== Preview & Rendering ==============

@router.post("/sample-data")
async def get_sample_data(req: Dict[str, Any]) -> Dict[str, Any]:
    """Get sample data for a given entity type."""
    entity_def = req.get("entity_def", "")
    
    # Generate realistic sample data based on entity type
    if "Contract" in entity_def:
        return {
            "Id": 12345,
            "Number": "CTR-2024-001",
            "Description": "Professional Services Agreement for Building Renovation",
            "Status": {"Name": "Active", "Id": 1},
            "Type": "Fixed Price",
            "Date": "2024-01-15T00:00:00Z",
            "ContractorCompany": {"ShortLabel": "ABC Construction LLC"},
            "ClientCompany": {"ShortLabel": "Client Corporation"},
            "OriginalContractAmount": 1250000,
            "CurrentContractAmount": 1375000,
            "ScheduleStart": "2024-02-01T00:00:00Z",
            "ScheduleEnd": "2024-08-31T00:00:00Z",
            "ScopeOfWork": "Complete renovation of Building A including HVAC, electrical, and plumbing.",
            "Author": {"ShortLabel": "John Smith"},
            "DomainPartition": {"Name": "Main Office Renovation", "Number": "PRJ-001"},
            "Items": [
                {"Number": "001", "Description": "Electrical Work", "TotalValue": 250000, "Status": "Complete"},
                {"Number": "002", "Description": "Plumbing Installation", "TotalValue": 185000, "Status": "In Progress"},
                {"Number": "003", "Description": "HVAC System", "TotalValue": 425000, "Status": "Pending"},
                {"Number": "004", "Description": "General Construction", "TotalValue": 350000, "Status": "In Progress"},
                {"Number": "005", "Description": "Finishing Work", "TotalValue": 165000, "Status": "Not Started"},
            ]
        }
    elif "RFI" in entity_def:
        return {
            "Number": "RFI-2024-042",
            "Subject": "Clarification on electrical panel placement",
            "Status": {"Name": "Open"},
            "Priority": {"Name": "High"},
            "DateRequired": "2024-02-15T00:00:00Z",
            "Question": "Please clarify the exact location for the main electrical panel per drawing E-101.",
            "Answer": "",
            "Author": {"ShortLabel": "Mike Johnson"},
            "AssignedTo": {"ShortLabel": "Sarah Williams"},
            "DomainPartition": {"Name": "Main Office Renovation"},
        }
    elif "PunchList" in entity_def:
        return {
            "Number": "PL-001",
            "Description": "Paint touch-up needed in conference room",
            "Status": {"Name": "Open"},
            "Priority": {"Name": "Medium"},
            "Location": "Building A, Floor 2, Room 201",
            "ResponsibleParty": {"ShortLabel": "ABC Painting Co"},
            "DueDate": "2024-03-01T00:00:00Z",
            "Notes": "Multiple areas showing brush marks",
            "DomainPartition": {"Name": "Main Office Renovation"},
        }
    else:
        return {
            "Number": "ITEM-001",
            "Description": "Sample Item",
            "Status": {"Name": "Active"},
            "CreatedDateTime": "2024-01-15T10:30:00Z",
        }


@router.post("/render-preview")
async def render_preview(req: RenderPreviewRequest):
    """Render a preview document from template and data."""
    from io import BytesIO
    from fastapi.responses import Response
    
    try:
        # Convert template dict to PortableTemplate
        template = PortableTemplate.from_dict(req.template)
        
        # Render to document
        renderer = TemplateRenderer()
        output_path, doc_bytes = renderer.render(template, req.data, filename="preview")
        
        # Return as downloadable file
        return Response(
            content=doc_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f"attachment; filename=\"{template.name or 'preview'}.docx\""
            }
        )
    except Exception as e:
        log.error(f"Render preview error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============== Template Generation ==============

class GenerateTemplateRequest(BaseModel):
    """Request to generate a new template from description."""
    name: str
    description: str
    entity_def: str


@router.post("/generate")
async def generate_template(req: GenerateTemplateRequest) -> Dict[str, Any]:
    """Generate a new template from a natural language description."""
    try:
        # Get entity schema dynamically from Kahua
        schema = await get_entity_schema(req.entity_def)
        available_fields = schema.get("attributes", [])
        
        # Use AI to analyze description and create template
        result = await analyze_document_description(
            description=req.description,
            target_entity_def=req.entity_def,
            available_fields=available_fields,
            user_guidance=f"Create a template named '{req.name}'"
        )
        
        if not result.success:
            return {"status": "error", "error": result.error}
        
        template = result.template
        template.name = req.name
        template.description = req.description[:500]
        
        return {
            "status": "ok",
            "template": template.to_dict(),
            "suggestions": result.suggestions or []
        }
    except Exception as e:
        log.error(f"Template generation error: {e}")
        return {"status": "error", "error": str(e)}


# ============== Document Editor Endpoints ==============

class SaveMarkdownRequest(BaseModel):
    """Request to save a markdown template."""
    name: str
    entityDef: str
    markdown: str
    description: str = ""


class AIInlineRequest(BaseModel):
    """Request for inline AI editing."""
    prompt: str
    context: str
    entityDef: str
    selectionStart: int
    selectionEnd: int


@router.post("/save-markdown")
async def save_markdown_template(req: SaveMarkdownRequest) -> Dict[str, Any]:
    """Save a markdown template to the templates directory."""
    import uuid
    from datetime import datetime
    
    try:
        # Generate template ID
        template_id = f"pv-{uuid.uuid4().hex[:8]}"
        
        # Create template data
        template_data = {
            "id": template_id,
            "name": req.name,
            "entity_def": req.entityDef,
            "description": req.description or f"Markdown template for {req.name}",
            "markdown": req.markdown,
            "created_at": datetime.now().isoformat(),
            "type": "markdown"
        }
        
        # Save to file
        filepath = PV_TEMPLATES_DIR / f"{template_id}.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(template_data, f, indent=2)
        
        log.info(f"Saved markdown template: {template_id} ({req.name})")
        
        return {
            "status": "ok",
            "template_id": template_id,
            "message": f"Template '{req.name}' saved successfully"
        }
    except Exception as e:
        log.error(f"Save markdown error: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/ai-inline")
async def ai_inline_edit(req: AIInlineRequest):
    """Process an inline AI edit request with streaming response."""
    from fastapi.responses import StreamingResponse
    
    try:
        log.info(f"AI inline request: {req.prompt[:100]}...")
        
        # Get the Anthropic client
        from pv_template_analyzer import get_anthropic_client
        client = get_anthropic_client()
        
        # Build the prompt
        selected_text = req.context[req.selectionStart:req.selectionEnd] if req.selectionStart < req.selectionEnd else ""
        
        system_prompt = f"""You are an expert at writing Jinja2 markdown templates for Kahua construction data.
The user is editing a template for entity type: {req.entityDef}

Template syntax rules:
- Use {{{{ field_path }}}} to insert entity field values
- Use {{{{ field_path | filter }}}} to apply filters (date, currency, default, upper, lower)
- Use {{% if condition %}} ... {{% endif %}} for conditionals
- Use {{% for item in Items %}} ... {{% endfor %}} for loops
- Use standard Markdown for formatting (# headings, **bold**, |tables|, etc.)

Common filters:
- | default('-') - show fallback if empty
- | currency - format as $1,234.56
- | date - format as Jan 15, 2024
- | upper / lower - change case

Available fields for {req.entityDef}:
Number, Subject, Description, Status.Name, Priority.Name, DateSubmitted, DateRequired,
Question, Answer, SubmittedBy.Name, AssignedTo.Name, CostImpact, ScheduleImpact

Output ONLY the generated template content - no explanations or markdown code fences."""

        user_prompt = f"""Current template:
```
{req.context}
```

{f"Selected text to replace: {selected_text}" if selected_text else "Cursor position for insertion."}

User request: {req.prompt}

Generate the template content:"""

        async def generate_stream():
            try:
                with client.messages.stream(
                    model="claude-sonnet-4-20250514",
                    max_tokens=2000,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}]
                ) as stream:
                    for text in stream.text_stream:
                        yield f"data: {json.dumps({'text': text})}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                log.error(f"AI stream error: {e}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
    except Exception as e:
        log.error(f"AI inline error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

