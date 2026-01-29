"""
Portable View Template Generator

Dynamic template generation for any Kahua entity type.
Creates reusable markdown templates that can be saved and customized.
"""

import os
import json
import uuid
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict

from pv_md_renderer import render_md_template, md_to_docx, REPORTS_DIR

log = logging.getLogger("pv_template_generator")

# Storage directories
TEMPLATES_DIR = Path(__file__).parent / "pv_templates" / "saved"
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

# In-memory preview cache
_preview_cache: Dict[str, Dict[str, Any]] = {}


@dataclass
class TemplateField:
    """A field to include in the template."""
    path: str  # e.g., "Status.Name" or "Amount"
    label: str  # Display label
    format: str = "text"  # text, currency, date, datetime, percent


@dataclass
class TemplateSection:
    """A section of the template."""
    type: str  # header, details, table, text
    title: Optional[str] = None
    fields: Optional[List[TemplateField]] = None
    content: Optional[str] = None  # For text sections


@dataclass
class GeneratedTemplate:
    """A dynamically generated template."""
    id: str
    name: str
    entity_def: str
    description: str
    sections: List[TemplateSection]
    created_at: str
    markdown: str  # The actual template markdown


# ============== Template Generation ==============

def generate_template_markdown(
    entity_name: str,
    title_field: str = "Number",
    subtitle_field: Optional[str] = "Description", 
    header_fields: List[Dict[str, str]] = None,
    detail_fields: List[Dict[str, str]] = None,
    table_config: Optional[Dict[str, Any]] = None,
    footer_text: Optional[str] = None,
) -> str:
    """
    Generate a markdown template for an entity.
    
    Args:
        entity_name: Display name (e.g., "RFI", "Contract")
        title_field: Field to use for main title
        subtitle_field: Field for subtitle (optional)
        header_fields: List of {path, label} for header key-value pairs
        detail_fields: List of {path, label, format} for detail section
        table_config: Config for child items table: {source, columns: [{path, label, format}]}
        footer_text: Optional footer text
    
    Returns:
        Markdown template string with Jinja2 syntax
    """
    lines = []
    
    # Title
    if subtitle_field:
        lines.append(f"# {{{{ {title_field} }}}} - {{{{ {subtitle_field} | default }}}}")
    else:
        lines.append(f"# {entity_name} #{{{{ {title_field} }}}}")
    
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Header section (key info in 2-column table)
    if header_fields:
        lines.append("| | |")
        lines.append("|:--|:--|")
        for f in header_fields:
            path = f.get('path', f.get('name', ''))
            label = f.get('label', path)
            fmt = f.get('format', 'text')
            value_expr = _format_expr(path, fmt)
            lines.append(f"| **{label}** | {value_expr} |")
        lines.append("")
    
    # Detail section
    if detail_fields:
        lines.append("## Details")
        lines.append("")
        lines.append("| Field | Value |")
        lines.append("|:------|:------|")
        for f in detail_fields:
            path = f.get('path', f.get('name', ''))
            label = f.get('label', path)
            fmt = f.get('format', 'text')
            value_expr = _format_expr(path, fmt)
            lines.append(f"| {label} | {value_expr} |")
        lines.append("")
    
    # Table section for child items
    if table_config:
        source = table_config.get('source', 'Items')
        columns = table_config.get('columns', [])
        
        lines.append(f"## {source}")
        lines.append("")
        lines.append(f"{{% if {source} %}}")
        
        # Table header
        headers = " | ".join(c.get('label', c.get('path', '')) for c in columns)
        lines.append(f"| {headers} |")
        
        # Separator
        sep = " | ".join("---" for _ in columns)
        lines.append(f"| {sep} |")
        
        # Row template
        lines.append(f"{{% for item in {source} %}}")
        cells = []
        for c in columns:
            path = c.get('path', c.get('name', ''))
            fmt = c.get('format', 'text')
            cells.append(_format_expr(f"item.{path}", fmt))
        lines.append(f"| {' | '.join(cells)} |")
        lines.append("{% endfor %}")
        lines.append("{% else %}")
        lines.append(f"*No {source.lower()} found.*")
        lines.append("{% endif %}")
        lines.append("")
    
    # Footer
    lines.append("---")
    lines.append("")
    if footer_text:
        lines.append(f"*{footer_text}*")
    else:
        lines.append("*Generated {{ _today }}*")
    
    return "\n".join(lines)


def _format_expr(path: str, fmt: str) -> str:
    """Create Jinja2 expression with formatting."""
    if fmt == "currency":
        return f"{{{{ {path} | currency }}}}"
    elif fmt == "date":
        return f"{{{{ {path} | date }}}}"
    elif fmt == "datetime":
        return f"{{{{ {path} | datetime }}}}"
    elif fmt == "percent":
        return f"{{{{ {path} }}}}%"
    else:
        return f"{{{{ {path} | default }}}}"


# ============== Template Creation Tool ==============

def create_entity_template(
    entity_def: str,
    entity_display_name: str,
    schema_fields: List[Dict[str, Any]],
    style: str = "professional",
    include_all_fields: bool = False,
) -> Dict[str, Any]:
    """
    Create a template for an entity based on its schema.
    
    Args:
        entity_def: Full entity definition (e.g., "kahua_AEC_RFI.RFI")
        entity_display_name: Human-readable name (e.g., "RFI")
        schema_fields: List of field dicts from get_entity_schema
        style: Template style - "professional", "simple", "detailed"
        include_all_fields: Include all fields vs smart selection
    
    Returns:
        Dict with template info and markdown
    """
    # Smart field selection based on entity type and field names
    header_fields = []
    detail_fields = []
    
    # Priority fields for header (key identifying info)
    header_priorities = ['Number', 'Name', 'Subject', 'Status', 'Project', 'DomainPartition']
    detail_priorities = ['Description', 'Type', 'Priority', 'Date', 'Amount', 'Value', 'From', 'To', 'AssignedTo', 'Author']
    
    for field in schema_fields:
        name = field.get('name', '')
        
        # Skip system fields
        if name.startswith('_') or name in ('Id', 'id', 'EntityDef'):
            continue
        
        field_info = {
            'path': name,
            'label': _humanize_label(name),
            'format': _infer_format(name, field.get('type', 'str'), field.get('sample', ''))
        }
        
        # Categorize
        if any(p.lower() in name.lower() for p in header_priorities):
            header_fields.append(field_info)
        elif include_all_fields or any(p.lower() in name.lower() for p in detail_priorities):
            detail_fields.append(field_info)
    
    # Limit fields for cleaner templates
    if not include_all_fields:
        header_fields = header_fields[:6]
        detail_fields = detail_fields[:10]
    
    # Determine title field
    title_field = "Number"
    subtitle_field = None
    for f in schema_fields:
        if f.get('name') in ('Subject', 'Name', 'Description'):
            subtitle_field = f.get('name')
            break
    
    # Generate markdown
    markdown = generate_template_markdown(
        entity_name=entity_display_name,
        title_field=title_field,
        subtitle_field=subtitle_field,
        header_fields=header_fields,
        detail_fields=detail_fields,
    )
    
    # Create template record
    template_id = f"pv-{uuid.uuid4().hex[:8]}"
    
    template = {
        "id": template_id,
        "name": f"{entity_display_name} Template",
        "entity_def": entity_def,
        "description": f"Auto-generated template for {entity_display_name}",
        "style": style,
        "created_at": datetime.now().isoformat(),
        "header_fields": header_fields,
        "detail_fields": detail_fields,
        "markdown": markdown,
    }
    
    return template


def _humanize_label(field_name: str) -> str:
    """Convert field name to human-readable label."""
    # Handle nested paths
    if '.' in field_name:
        field_name = field_name.split('.')[-1]
    
    # Handle camelCase and PascalCase
    import re
    words = re.sub(r'([a-z])([A-Z])', r'\1 \2', field_name)
    words = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1 \2', words)
    return words.replace('_', ' ').title()


def _infer_format(name: str, type_name: str, sample: str) -> str:
    """Infer the display format for a field."""
    name_lower = name.lower()
    
    if any(x in name_lower for x in ['amount', 'value', 'price', 'cost', 'total']):
        return 'currency'
    if any(x in name_lower for x in ['date', 'created', 'modified', 'due']):
        return 'date'
    if 'percent' in name_lower:
        return 'percent'
    if type_name in ('float', 'int') and sample:
        try:
            val = float(sample)
            if val > 100:  # Likely currency
                return 'currency'
        except:
            pass
    
    return 'text'


# ============== Preview System ==============

def preview_template(
    template_id: str,
    template_markdown: str,
    entity_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Preview a template with actual entity data.
    
    Args:
        template_id: Template identifier
        template_markdown: The markdown template content
        entity_data: Actual entity data to render
    
    Returns:
        Dict with preview_id and rendered markdown
    """
    try:
        rendered = render_md_template(template_markdown, entity_data)
        
        preview_id = f"preview-{uuid.uuid4().hex[:8]}"
        
        # Cache for finalization
        _preview_cache[preview_id] = {
            "template_id": template_id,
            "template_markdown": template_markdown,
            "rendered_markdown": rendered,
            "entity_data": entity_data,
            "created_at": datetime.now().isoformat(),
        }
        
        return {
            "status": "ok",
            "preview_id": preview_id,
            "template_id": template_id,
            "rendered_markdown": rendered,
            "message": "Preview generated. Review the content above and let me know if you'd like any changes."
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Preview failed: {str(e)}"
        }


def finalize_preview(preview_id: str, output_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Finalize a preview and generate DOCX.
    
    Args:
        preview_id: Preview identifier from preview_template
        output_name: Optional custom output filename
    
    Returns:
        Dict with download URL
    """
    if preview_id not in _preview_cache:
        return {"status": "error", "message": f"Preview {preview_id} not found or expired"}
    
    preview = _preview_cache[preview_id]
    rendered_md = preview["rendered_markdown"]
    
    if not output_name:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_name = f"document_{timestamp}"
    
    output_path = REPORTS_DIR / f"{output_name}.docx"
    
    try:
        md_to_docx(rendered_md, output_path)
        
        base_url = os.getenv("REPORT_BASE_URL", "http://localhost:8000")
        download_url = f"{base_url}/reports/{output_name}.docx"
        
        # Clean up cache
        del _preview_cache[preview_id]
        
        return {
            "status": "ok",
            "filename": f"{output_name}.docx",
            "download_url": download_url,
            "message": f"Document generated! Download: {download_url}"
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to generate document: {str(e)}"}


# ============== Template Storage ==============

def save_template(
    template_id: str,
    name: str,
    entity_def: str,
    markdown: str,
    description: str = "",
) -> Dict[str, Any]:
    """
    Save a template for reuse.
    
    Args:
        template_id: Template identifier
        name: Human-readable template name
        entity_def: Target entity definition
        markdown: The markdown template content
        description: Optional description
    
    Returns:
        Dict with save status
    """
    template_data = {
        "id": template_id,
        "name": name,
        "entity_def": entity_def,
        "description": description,
        "markdown": markdown,
        "created_at": datetime.now().isoformat(),
    }
    
    filepath = TEMPLATES_DIR / f"{template_id}.json"
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(template_data, f, indent=2)
        
        return {
            "status": "ok",
            "template_id": template_id,
            "filepath": str(filepath),
            "message": f"Template '{name}' saved successfully. You can reuse it anytime."
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to save template: {str(e)}"}


def load_template(template_id: str) -> Dict[str, Any]:
    """Load a saved template."""
    filepath = TEMPLATES_DIR / f"{template_id}.json"
    
    if not filepath.exists():
        return {"status": "error", "message": f"Template {template_id} not found"}
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            template_data = json.load(f)
        return {"status": "ok", "template": template_data}
    except Exception as e:
        return {"status": "error", "message": f"Failed to load template: {str(e)}"}


def list_saved_templates(entity_def: Optional[str] = None) -> Dict[str, Any]:
    """List all saved templates, optionally filtered by entity."""
    templates = []
    
    for filepath in TEMPLATES_DIR.glob("*.json"):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if entity_def and data.get("entity_def") != entity_def:
                continue
            
            templates.append({
                "id": data.get("id"),
                "name": data.get("name"),
                "entity_def": data.get("entity_def"),
                "description": data.get("description", ""),
                "created_at": data.get("created_at"),
            })
        except:
            continue
    
    return {
        "status": "ok",
        "templates": templates,
        "count": len(templates),
    }


def update_template_markdown(template_id: str, new_markdown: str) -> Dict[str, Any]:
    """
    Update the markdown content of a template.
    
    Args:
        template_id: Template to update (can be preview ID or saved template ID)
        new_markdown: Updated markdown content
    
    Returns:
        Dict with status
    """
    # Check if it's a preview
    if template_id in _preview_cache:
        _preview_cache[template_id]["template_markdown"] = new_markdown
        # Re-render with new markdown
        entity_data = _preview_cache[template_id]["entity_data"]
        try:
            rendered = render_md_template(new_markdown, entity_data)
            _preview_cache[template_id]["rendered_markdown"] = rendered
            return {
                "status": "ok",
                "rendered_markdown": rendered,
                "message": "Template updated. Here's the new preview:"
            }
        except Exception as e:
            return {"status": "error", "message": f"Invalid template: {str(e)}"}
    
    # Check saved templates
    filepath = TEMPLATES_DIR / f"{template_id}.json"
    if filepath.exists():
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            data["markdown"] = new_markdown
            data["updated_at"] = datetime.now().isoformat()
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            return {"status": "ok", "message": "Template updated and saved."}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    return {"status": "error", "message": f"Template {template_id} not found"}
