"""
Portable View Template Agent Tools
Tools for the AI agent to create, manage, and render portable templates.

DEPRECATED: This module is not imported anywhere. 
Use langgraph_agent.py tools or report_genius.agent instead.
"""

import warnings
warnings.warn(
    "pv_template_tools is deprecated and not used. "
    "Use langgraph_agent.py or report_genius.agent instead.",
    DeprecationWarning,
    stacklevel=2
)

import os
import json
import base64
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

# Import from agents SDK
try:
    from agents import function_tool
except ImportError:
    # Fallback decorator if agents SDK not available
    def function_tool(func):
        return func

from pv_template_schema import (
    PortableTemplate, Section, SectionType, FieldMapping, FieldFormat,
    EXAMPLE_CONTRACT_TEMPLATE, EXAMPLE_DAILY_REPORT_TEMPLATE,
    create_simple_report_template, create_table_report_template
)
from pv_template_analyzer import (
    analyze_document_image, analyze_document_description, 
    refine_template, extract_image_from_pdf, AnalysisResult
)
from pv_template_renderer import TemplateRenderer, render_template

log = logging.getLogger("pv_template_tools")

# Template storage (using existing template store infrastructure)
from templates import get_template_store


# ============== Template Storage Helpers ==============

def _save_pv_template(template: PortableTemplate) -> str:
    """Save a portable template to storage."""
    # Generate ID if needed
    if not template.id:
        import uuid
        template.id = f"pv-{uuid.uuid4().hex[:8]}"
    
    now = datetime.utcnow().isoformat()
    template.created_at = template.created_at or now
    template.updated_at = now
    
    # Store as JSON in templates directory
    templates_dir = Path(__file__).parent / "pv_templates" / "saved"
    templates_dir.mkdir(parents=True, exist_ok=True)
    
    filepath = templates_dir / f"{template.id}.json"
    with open(filepath, 'w') as f:
        f.write(template.to_json())
    
    return template.id


def _load_pv_template(template_id: str) -> Optional[PortableTemplate]:
    """Load a portable template from storage."""
    templates_dir = Path(__file__).parent / "pv_templates" / "saved"
    filepath = templates_dir / f"{template_id}.json"
    
    if not filepath.exists():
        # Check built-in examples
        if template_id == "example-contract":
            return EXAMPLE_CONTRACT_TEMPLATE
        elif template_id == "example-daily-report":
            return EXAMPLE_DAILY_REPORT_TEMPLATE
        return None
    
    with open(filepath, 'r') as f:
        return PortableTemplate.from_json(f.read())


def _list_pv_templates(category: str = None, search: str = None) -> List[Dict[str, Any]]:
    """List available portable templates."""
    templates = []
    
    # Built-in examples
    examples = [
        {"id": "example-contract", "name": "Contract Summary", "category": "cost", "entity": "kahua_Contract.Contract"},
        {"id": "example-daily-report", "name": "Daily Report", "category": "field", "entity": "kahua_AEC_DailyReport.DailyReport"},
    ]
    templates.extend(examples)
    
    # Saved templates
    templates_dir = Path(__file__).parent / "pv_templates" / "saved"
    if templates_dir.exists():
        for f in templates_dir.glob("*.json"):
            try:
                with open(f, 'r') as fp:
                    data = json.load(fp)
                    templates.append({
                        "id": data.get("id", f.stem),
                        "name": data.get("name", "Untitled"),
                        "category": data.get("category", "custom"),
                        "entity": data.get("target_entity_def", ""),
                        "description": data.get("description", "")[:100]
                    })
            except:
                pass
    
    # Filter
    if category:
        templates = [t for t in templates if t.get("category") == category]
    if search:
        search_lower = search.lower()
        templates = [t for t in templates if search_lower in t.get("name", "").lower() or search_lower in t.get("description", "").lower()]
    
    return templates


# ============== Agent Tools ==============

@function_tool
async def list_portable_templates(
    category: Optional[str] = None,
    search: Optional[str] = None
) -> dict:
    """
    List available portable view templates for report generation.
    
    Args:
        category: Filter by category. Options: "cost", "field", "executive", "custom"
        search: Search term to filter by name or description
    
    Returns:
        Dict with list of templates including IDs, names, categories, and target entities.
    """
    try:
        templates = _list_pv_templates(category=category, search=search)
        return {
            "status": "ok",
            "count": len(templates),
            "templates": templates
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@function_tool
async def get_portable_template(template_id: str) -> dict:
    """
    Get details of a specific portable template.
    
    Args:
        template_id: The ID of the template to retrieve
    
    Returns:
        Full template definition including sections and field mappings.
    """
    try:
        template = _load_pv_template(template_id)
        if not template:
            return {"status": "error", "error": f"Template '{template_id}' not found"}
        
        return {
            "status": "ok",
            "template": template.to_dict()
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@function_tool
async def create_template_from_description(
    name: str,
    description: str,
    target_entity_def: str,
    user_guidance: Optional[str] = None,
    available_fields_json: Optional[str] = None
) -> dict:
    """
    Create a new portable template from a natural language description.
    
    Use this when the user describes what kind of report they want.
    
    Args:
        name: Name for the new template
        description: Detailed description of desired report layout and content
        target_entity_def: The Kahua entity type (e.g., "kahua_Contract.Contract")
        user_guidance: Additional specific instructions
        available_fields_json: JSON string of available fields from schema discovery
    
    Returns:
        The created template with ID for future use.
    """
    try:
        # Parse available_fields from JSON
        available_fields = []
        if available_fields_json:
            try:
                available_fields = json.loads(available_fields_json)
            except json.JSONDecodeError:
                pass
        
        # Analyze description to create template
        result = await analyze_document_description(
            description=description,
            target_entity_def=target_entity_def,
            available_fields=available_fields,
            user_guidance=user_guidance or ""
        )
        
        if not result.success:
            return {"status": "error", "error": result.error}
        
        template = result.template
        template.name = name
        template.description = description[:500]
        
        # Save template
        template_id = _save_pv_template(template)
        
        return {
            "status": "ok",
            "template_id": template_id,
            "template": template.to_dict(),
            "suggestions": result.suggestions
        }
    except Exception as e:
        log.error(f"Template creation failed: {e}")
        return {"status": "error", "error": str(e)}


@function_tool
async def create_template_from_image(
    name: str,
    image_base64: str,
    target_entity_def: str,
    user_guidance: Optional[str] = None,
    available_fields_json: Optional[str] = None
) -> dict:
    """
    Create a template by analyzing an uploaded document image.
    
    Use this when the user uploads a PDF, screenshot, or image of an example report.
    
    Args:
        name: Name for the new template
        image_base64: Base64 encoded image data
        target_entity_def: The Kahua entity type for this template
        user_guidance: What specific aspects to capture from the example
        available_fields_json: JSON string of available fields from schema discovery
    
    Returns:
        The created template with ID, plus analysis details.
    """
    try:
        image_data = base64.b64decode(image_base64)
        
        # Parse available_fields from JSON
        available_fields = []
        if available_fields_json:
            try:
                available_fields = json.loads(available_fields_json)
            except json.JSONDecodeError:
                pass
        
        result = await analyze_document_image(
            image_data=image_data,
            target_entity_def=target_entity_def,
            available_fields=available_fields,
            user_guidance=user_guidance or ""
        )
        
        if not result.success:
            return {"status": "error", "error": result.error}
        
        template = result.template
        template.name = name
        template.source_type = "image"
        
        template_id = _save_pv_template(template)
        
        return {
            "status": "ok",
            "template_id": template_id,
            "template": template.to_dict(),
            "identified_sections": result.identified_sections,
            "field_mappings": result.field_mappings,
            "suggestions": result.suggestions
        }
    except Exception as e:
        log.error(f"Image analysis failed: {e}")
        return {"status": "error", "error": str(e)}


@function_tool
async def refine_portable_template(
    template_id: str,
    instruction: str,
    available_fields_json: Optional[str] = None
) -> dict:
    """
    Modify an existing template based on user instruction.
    
    Use this for iterative refinement - "make the header bigger", "add a column", etc.
    
    Args:
        template_id: ID of template to modify
        instruction: Natural language modification request
        available_fields_json: Optional JSON string of available fields for context
    
    Returns:
        Updated template and list of changes made.
    """
    try:
        template = _load_pv_template(template_id)
        if not template:
            return {"status": "error", "error": f"Template '{template_id}' not found"}
        
        # Parse available_fields from JSON
        available_fields = None
        if available_fields_json:
            try:
                available_fields = json.loads(available_fields_json)
            except json.JSONDecodeError:
                pass
        
        modified, changes = await refine_template(
            template=template,
            instruction=instruction,
            available_fields=available_fields
        )
        
        # Save updated template
        _save_pv_template(modified)
        
        return {
            "status": "ok",
            "template_id": modified.id,
            "template": modified.to_dict(),
            "changes_made": changes
        }
    except Exception as e:
        log.error(f"Template refinement failed: {e}")
        return {"status": "error", "error": str(e)}


@function_tool
async def render_portable_template(
    template_id: str,
    entity_data_json: str,
    filename: Optional[str] = None
) -> dict:
    """
    Generate a Word document from a portable template and entity data.
    
    Args:
        template_id: ID of the template to use
        entity_data_json: JSON string of entity data to populate the template.
            Can be either:
            - Direct entity object: {"Number": "001", "Status": "Open", ...}
            - Query result: {"entities": [{"Number": "001", ...}], "count": 1}
            - Single item from entities array
        filename: Optional custom filename for the output
    
    Returns:
        Path to generated document and download URL.
    """
    try:
        template = _load_pv_template(template_id)
        if not template:
            return {"status": "error", "error": f"Template '{template_id}' not found"}
        
        # Parse entity_data from JSON
        try:
            entity_data = json.loads(entity_data_json)
        except json.JSONDecodeError as e:
            return {"status": "error", "error": f"Invalid entity_data_json: {e}"}
        
        # Extract actual entity if wrapped in query result structure
        if isinstance(entity_data, dict):
            # Check for query result wrapper
            if "entities" in entity_data and isinstance(entity_data["entities"], list):
                if entity_data["entities"]:
                    entity_data = entity_data["entities"][0]  # Use first entity
                else:
                    return {"status": "error", "error": "No entities in query result"}
            # Also check for sets structure from Kahua
            elif "sets" in entity_data and isinstance(entity_data["sets"], list):
                for s in entity_data["sets"]:
                    if isinstance(s.get("entities"), list) and s["entities"]:
                        entity_data = s["entities"][0]
                        break
        
        renderer = TemplateRenderer()
        output_path, doc_bytes = renderer.render(template, entity_data, filename)
        
        # Construct full URL for download
        base_url = os.getenv("REPORT_BASE_URL", "http://localhost:8000")
        download_url = f"{base_url}/reports/{output_path.name}"
        
        return {
            "status": "ok",
            "filename": output_path.name,
            "path": str(output_path),
            "download_url": download_url,
            "message": f"Report generated! Download here: {download_url}",
            "size_bytes": len(doc_bytes)
        }
    except Exception as e:
        log.error(f"Template rendering failed: {e}")
        return {"status": "error", "error": str(e)}


@function_tool
async def create_quick_template(
    name: str,
    target_entity_def: str,
    template_type: str,
    header_fields: List[str],
    detail_fields: Optional[List[str]] = None,
    table_source: Optional[str] = None,
    table_columns_json: Optional[str] = None,
    description: Optional[str] = None
) -> dict:
    """
    Quickly create a template using predefined patterns.
    
    Args:
        name: Template name
        target_entity_def: Entity type (e.g., "kahua_Contract.Contract")
        template_type: "simple" (header + details) or "table" (header + table)
        header_fields: Fields to show in header (e.g., ["Number", "Status.Name"])
        detail_fields: Fields for detail section (for "simple" type)
        table_source: Child collection path (for "table" type, e.g., "Items")
        table_columns_json: JSON string of column definitions (for "table" type), e.g. '[{"path": "Number", "label": "#"}]'
        description: Optional template description
    
    Returns:
        Created template with ID.
    """
    try:
        # Parse table_columns from JSON
        table_columns = None
        if table_columns_json:
            try:
                table_columns = json.loads(table_columns_json)
            except json.JSONDecodeError:
                table_columns = [{"path": "Number"}, {"path": "Description"}]
        
        if template_type == "simple":
            template = create_simple_report_template(
                name=name,
                entity_def=target_entity_def,
                header_fields=header_fields,
                detail_fields=detail_fields or [],
                description=description or ""
            )
        elif template_type == "table":
            template = create_table_report_template(
                name=name,
                entity_def=target_entity_def,
                header_fields=header_fields,
                table_source=table_source or "Items",
                table_columns=table_columns or [{"path": "Number"}, {"path": "Description"}],
                description=description or ""
            )
        else:
            return {"status": "error", "error": f"Unknown template type: {template_type}"}
        
        template_id = _save_pv_template(template)
        
        return {
            "status": "ok",
            "template_id": template_id,
            "template": template.to_dict()
        }
    except Exception as e:
        log.error(f"Quick template creation failed: {e}")
        return {"status": "error", "error": str(e)}


@function_tool
async def delete_portable_template(template_id: str) -> dict:
    """
    Delete a portable template.
    
    Args:
        template_id: ID of template to delete
    
    Returns:
        Confirmation of deletion.
    """
    try:
        if template_id.startswith("example-"):
            return {"status": "error", "error": "Cannot delete built-in example templates"}
        
        templates_dir = Path(__file__).parent / "pv_templates" / "saved"
        filepath = templates_dir / f"{template_id}.json"
        
        if not filepath.exists():
            return {"status": "error", "error": f"Template '{template_id}' not found"}
        
        filepath.unlink()
        
        return {"status": "ok", "deleted": template_id}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@function_tool
async def browse_kahua_files(
    project_id: int = 0, 
    file_type: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 20
) -> dict:
    """
    Browse files stored in Kahua (documents, images, photos).
    Use this to find images for reports or see available documents.
    
    Args:
        project_id: Project to browse. Use 0 for domain-wide.
        file_type: Filter by type: "image", "document", "drawing", or None for all.
        search: Optional search term for filename.
        limit: Max files to return (default 20).
    
    Returns:
        List of files with IDs, names, types, and download info.
    """
    import httpx
    
    # Import auth from agents_superagent
    try:
        from agents_superagent import QUERY_URL_TEMPLATE, HEADERS_JSON
    except ImportError:
        return {"status": "error", "error": "Could not import Kahua auth"}
    
    query_url = QUERY_URL_TEMPLATE.format(project_id=project_id)
    
    qpayload = {
        "PropertyName": "Query",
        "EntityDef": "kahua_FileManager.File",
        "Take": str(limit),
        "Partition": {"Scope": "Any"}
    }
    
    # Add conditions for file type filtering
    conditions = []
    if file_type == "image":
        conditions.append({
            "PropertyName": "Condition",
            "Path": "ContentType",
            "Type": "StartsWith",
            "Value": "image/"
        })
    elif file_type == "document":
        conditions.append({
            "PropertyName": "Condition", 
            "Path": "ContentType",
            "Type": "In",
            "Values": ["application/pdf", "application/msword", 
                      "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
        })
    
    if search:
        conditions.append({
            "PropertyName": "Condition",
            "Path": "Name",
            "Type": "Contains",
            "Value": search
        })
    
    if conditions:
        qpayload["Conditions"] = conditions
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(query_url, headers=HEADERS_JSON(), json=qpayload)
            if resp.status_code >= 400:
                return {"status": "error", "code": resp.status_code}
            body = resp.json()
    except Exception as e:
        return {"status": "error", "error": str(e)}
    
    # Extract files
    files = []
    entities = body.get("entities", [])
    for s in body.get("sets", []):
        if isinstance(s.get("entities"), list):
            entities = s["entities"]
            break
    
    for f in entities[:limit]:
        file_info = {
            "id": f.get("Id"),
            "name": f.get("Name", f.get("FileName", "")),
            "content_type": f.get("ContentType", ""),
            "size": f.get("FileSize", 0),
            "created": f.get("CreatedDateTime", ""),
            "is_image": str(f.get("ContentType", "")).startswith("image/")
        }
        files.append(file_info)
    
    return {
        "status": "ok",
        "count": len(files),
        "files": files,
        "tip": "Use file IDs with download_kahua_file() to get file content for reports"
    }


@function_tool
async def download_kahua_file(file_id: str, project_id: int = 0) -> dict:
    """
    Download a file from Kahua by its ID.
    Returns the file saved locally, ready to embed in reports.
    
    Args:
        file_id: The Kahua file entity ID.
        project_id: Project context (use 0 for domain-wide).
    
    Returns:
        Local file path and metadata.
    """
    import httpx
    
    try:
        from agents_superagent import HEADERS_JSON
    except ImportError:
        return {"status": "error", "error": "Could not import Kahua auth"}
    
    # Kahua file download URL pattern
    download_url = f"https://demo01service.kahua.com/v2/domains/Summit/projects/{project_id}/files/{file_id}/content"
    
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            resp = await client.get(download_url, headers=HEADERS_JSON())
            if resp.status_code >= 400:
                return {"status": "error", "code": resp.status_code, "message": "File not found or access denied"}
            
            # Get filename from headers or use ID
            content_disp = resp.headers.get("content-disposition", "")
            if "filename=" in content_disp:
                import re
                match = re.search(r'filename="?([^";\n]+)"?', content_disp)
                filename = match.group(1) if match else f"file_{file_id}"
            else:
                content_type = resp.headers.get("content-type", "application/octet-stream")
                ext = ".bin"
                if "image/jpeg" in content_type:
                    ext = ".jpg"
                elif "image/png" in content_type:
                    ext = ".png"
                elif "application/pdf" in content_type:
                    ext = ".pdf"
                filename = f"file_{file_id}{ext}"
            
            # Save to downloads directory
            downloads_dir = Path(__file__).parent / "downloads"
            downloads_dir.mkdir(exist_ok=True)
            
            local_path = downloads_dir / filename
            local_path.write_bytes(resp.content)
            
            return {
                "status": "ok",
                "filename": filename,
                "path": str(local_path),
                "size_bytes": len(resp.content),
                "content_type": resp.headers.get("content-type"),
                "is_image": resp.headers.get("content-type", "").startswith("image/")
            }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@function_tool  
async def upload_local_file(file_path: str) -> dict:
    """
    Register a local file (image, docx, pdf) for use in reports.
    Use this when the user provides a file path or pastes content.
    
    Args:
        file_path: Absolute path to the local file.
    
    Returns:
        File info and path for embedding in templates.
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return {"status": "error", "error": f"File not found: {file_path}"}
        
        # Copy to uploads directory for consistency
        uploads_dir = Path(__file__).parent / "uploads"
        uploads_dir.mkdir(exist_ok=True)
        
        import shutil
        dest_path = uploads_dir / path.name
        shutil.copy2(path, dest_path)
        
        # Determine file type
        suffix = path.suffix.lower()
        file_type = "unknown"
        if suffix in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]:
            file_type = "image"
        elif suffix in [".pdf"]:
            file_type = "pdf"
        elif suffix in [".docx", ".doc"]:
            file_type = "word"
        elif suffix in [".xlsx", ".xls"]:
            file_type = "excel"
        
        return {
            "status": "ok",
            "filename": path.name,
            "path": str(dest_path),
            "type": file_type,
            "size_bytes": dest_path.stat().st_size,
            "message": f"File ready for use in reports. Path: {dest_path}"
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ============== Markdown-based Portable View Tools ==============

# Directory for MD templates
PV_MD_TEMPLATES_DIR = Path(__file__).parent / "pv_templates"


def _list_md_templates() -> List[Dict[str, Any]]:
    """List available markdown templates."""
    templates = []
    if PV_MD_TEMPLATES_DIR.exists():
        for f in PV_MD_TEMPLATES_DIR.glob("*.md"):
            # Read first line for title
            content = f.read_text(encoding='utf-8')
            first_line = content.split('\n')[0] if content else ""
            name = first_line.lstrip('#').strip() if first_line.startswith('#') else f.stem
            templates.append({
                "id": f.stem,
                "name": name,
                "path": str(f),
                "type": "markdown"
            })
    return templates


@function_tool
async def list_md_templates() -> dict:
    """
    List available Markdown-based portable view templates.
    
    These templates use Jinja2 syntax for easy customization.
    
    Returns:
        List of available templates with IDs and names.
    """
    templates = _list_md_templates()
    return {
        "status": "ok",
        "templates": templates,
        "count": len(templates)
    }


@function_tool
async def preview_md_portable_view(
    template_id: str,
    entity_data_json: str
) -> dict:
    """
    Preview a portable view as rendered Markdown BEFORE generating the document.
    
    ALWAYS use this first to show the user what the document will look like.
    Display the returned markdown in the chat and ask for approval before finalizing.
    
    Args:
        template_id: ID of the markdown template (filename without .md)
        entity_data_json: JSON string of entity data
    
    Returns:
        Rendered markdown for display, plus a preview_id to use for finalization.
    """
    try:
        from pv_md_renderer import preview_portable_view
        
        template_path = PV_MD_TEMPLATES_DIR / f"{template_id}.md"
        if not template_path.exists():
            return {"status": "error", "error": f"Template '{template_id}' not found"}
        
        # Parse entity data
        try:
            entity_data = json.loads(entity_data_json)
        except json.JSONDecodeError as e:
            return {"status": "error", "error": f"Invalid JSON: {e}"}
        
        # Handle wrapped data formats
        if isinstance(entity_data, dict):
            if "entities" in entity_data and isinstance(entity_data["entities"], list):
                if entity_data["entities"]:
                    entity_data = entity_data["entities"][0]
                else:
                    return {"status": "error", "error": "No entities in data"}
            elif "sets" in entity_data:
                for s in entity_data.get("sets", []):
                    if isinstance(s.get("entities"), list) and s["entities"]:
                        entity_data = s["entities"][0]
                        break
        
        # Render preview
        rendered_md = preview_portable_view(template_path, entity_data)
        
        # Generate preview ID for later finalization
        import hashlib
        preview_id = hashlib.md5(rendered_md.encode()).hexdigest()[:12]
        
        # Cache the rendered content for finalization
        cache_path = Path(__file__).parent / "reports" / f".preview_{preview_id}.md"
        cache_path.write_text(rendered_md, encoding='utf-8')
        
        return {
            "status": "ok",
            "preview_id": preview_id,
            "template_id": template_id,
            "rendered_markdown": rendered_md,
            "message": "Here's a preview of the document. Let me know if you'd like any changes, or say 'looks good' to generate the final document."
        }
    except Exception as e:
        log.error(f"Preview failed: {e}")
        return {"status": "error", "error": str(e)}


@function_tool
async def finalize_md_portable_view(
    preview_id: str,
    output_name: Optional[str] = None
) -> dict:
    """
    Generate the final DOCX document from a previously previewed portable view.
    
    Only call this AFTER the user has approved the preview.
    
    Args:
        preview_id: The preview_id returned from preview_md_portable_view
        output_name: Optional custom filename (without extension)
    
    Returns:
        Download URL for the generated document.
    """
    try:
        from pv_md_renderer import finalize_portable_view
        
        # Load cached preview
        cache_path = Path(__file__).parent / "reports" / f".preview_{preview_id}.md"
        if not cache_path.exists():
            return {"status": "error", "error": "Preview not found. Please generate a new preview first."}
        
        rendered_md = cache_path.read_text(encoding='utf-8')
        
        # Generate output name if not provided
        if not output_name:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_name = f"portable_view_{timestamp}"
        
        # Convert to DOCX
        output_path = finalize_portable_view(rendered_md, output_name)
        
        # Cleanup cache
        cache_path.unlink(missing_ok=True)
        
        # Build download URL
        base_url = os.getenv("REPORT_BASE_URL", "http://localhost:8000")
        download_url = f"{base_url}/reports/{output_path.name}"
        
        return {
            "status": "ok",
            "filename": output_path.name,
            "download_url": download_url,
            "message": f"Document generated! [Download {output_path.name}]({download_url})"
        }
    except Exception as e:
        log.error(f"Finalization failed: {e}")
        return {"status": "error", "error": str(e)}


# ============== Export all tools ==============

PV_TEMPLATE_TOOLS = [
    list_portable_templates,
    get_portable_template,
    create_template_from_description,
    create_template_from_image,
    refine_portable_template,
    render_portable_template,
    create_quick_template,
    delete_portable_template,
    browse_kahua_files,
    download_kahua_file,
    upload_local_file,
    # New MD-based tools
    list_md_templates,
    preview_md_portable_view,
    finalize_md_portable_view,
]
