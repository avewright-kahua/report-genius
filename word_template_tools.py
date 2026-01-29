"""
Word Template Agent Tools
Tools for AI agents to create, manage, and render Word templates.
"""

import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

# Import from agents SDK
try:
    from agents import function_tool
except ImportError:
    def function_tool(func):
        return func

from word_template_defs import (
    WordTemplateDef, Section, SectionKind, ThemeDef, Condition,
    FieldDef, ColumnDef, FieldFormat, Alignment, Orientation,
    TitleSection, HeaderSection, FieldGridSection, DataTableSection,
    TextSection, ImageSection, SignatureSection, SpacerSection,
    TemplateRegistry, get_registry,
    create_field, create_column, create_title_section, create_header_section,
    create_field_grid_section, create_table_section, create_text_section,
    get_contract_template, get_rfi_template
)
from word_template_renderer import (
    WordTemplateRenderer, render_template, render_template_to_bytes, quick_render
)

log = logging.getLogger("word_template_tools")


# ============== Template Management Tools ==============

@function_tool
async def list_word_templates(
    category: Optional[str] = None,
    entity_def: Optional[str] = None,
    search: Optional[str] = None
) -> dict:
    """
    List available Word templates.
    
    Args:
        category: Filter by category (e.g., "cost", "field", "executive", "custom")
        entity_def: Filter by target entity definition
        search: Search term for name/description
    
    Returns:
        Dict with list of templates
    """
    try:
        registry = get_registry()
        templates = registry.list_all(category=category, entity_def=entity_def, search=search)
        
        # Add built-in templates
        builtins = [
            {"id": "builtin-contract", "name": "Contract Summary", "category": "cost", 
             "entity_def": "kahua_Contract.Contract", "description": "Professional contract portable view"},
            {"id": "builtin-rfi", "name": "RFI Summary", "category": "field",
             "entity_def": "kahua_AEC_RFI.RFI", "description": "Request for Information view"},
        ]
        
        # Filter builtins too
        for b in builtins:
            if category and b["category"] != category:
                continue
            if entity_def and b["entity_def"] != entity_def:
                continue
            if search and search.lower() not in b["name"].lower() and search.lower() not in b["description"].lower():
                continue
            templates.insert(0, b)
        
        return {
            "status": "ok",
            "count": len(templates),
            "templates": templates
        }
    except Exception as e:
        log.error(f"Error listing templates: {e}")
        return {"status": "error", "error": str(e)}


@function_tool
async def get_word_template(template_id: str) -> dict:
    """
    Get full details of a Word template.
    
    Args:
        template_id: Template ID to retrieve
    
    Returns:
        Full template definition as dict
    """
    try:
        # Check for built-in templates
        if template_id == "builtin-contract":
            template = get_contract_template()
        elif template_id == "builtin-rfi":
            template = get_rfi_template()
        else:
            registry = get_registry()
            template = registry.load(template_id)
        
        if not template:
            return {"status": "error", "error": f"Template '{template_id}' not found"}
        
        return {
            "status": "ok",
            "template": template.to_dict()
        }
    except Exception as e:
        log.error(f"Error getting template: {e}")
        return {"status": "error", "error": str(e)}


@function_tool
async def save_word_template(template_json: str) -> dict:
    """
    Save or update a Word template.
    
    Args:
        template_json: Full template definition as JSON string
    
    Returns:
        Saved template ID
    """
    try:
        template = WordTemplateDef.from_json(template_json)
        registry = get_registry()
        template_id = registry.save(template)
        
        return {
            "status": "ok",
            "template_id": template_id,
            "message": f"Template '{template.name}' saved successfully"
        }
    except Exception as e:
        log.error(f"Error saving template: {e}")
        return {"status": "error", "error": str(e)}


@function_tool
async def delete_word_template(template_id: str) -> dict:
    """
    Delete a Word template.
    
    Args:
        template_id: ID of template to delete
    
    Returns:
        Success status
    """
    try:
        if template_id.startswith("builtin-"):
            return {"status": "error", "error": "Cannot delete built-in templates"}
        
        registry = get_registry()
        success = registry.delete(template_id)
        
        if success:
            return {"status": "ok", "message": f"Template '{template_id}' deleted"}
        else:
            return {"status": "error", "error": f"Template '{template_id}' not found"}
    except Exception as e:
        log.error(f"Error deleting template: {e}")
        return {"status": "error", "error": str(e)}


@function_tool
async def duplicate_word_template(template_id: str, new_name: Optional[str] = None) -> dict:
    """
    Duplicate an existing template.
    
    Args:
        template_id: ID of template to duplicate
        new_name: Name for the new template
    
    Returns:
        New template ID
    """
    try:
        registry = get_registry()
        
        # Handle built-in templates
        if template_id == "builtin-contract":
            template = get_contract_template()
        elif template_id == "builtin-rfi":
            template = get_rfi_template()
        else:
            template = registry.load(template_id)
        
        if not template:
            return {"status": "error", "error": f"Template '{template_id}' not found"}
        
        # Create copy
        template.id = None
        template.name = new_name or f"{template.name} (Copy)"
        template.created_at = None
        template.updated_at = None
        
        new_id = registry.save(template)
        
        return {
            "status": "ok",
            "template_id": new_id,
            "message": f"Template duplicated as '{template.name}'"
        }
    except Exception as e:
        log.error(f"Error duplicating template: {e}")
        return {"status": "error", "error": str(e)}


# ============== Template Creation Tools ==============

@function_tool
async def create_word_template(
    name: str,
    description: str,
    entity_def: str,
    sections_json: str,
    theme_json: Optional[str] = None,
    category: str = "custom",
    tags: Optional[str] = None
) -> dict:
    """
    Create a new Word template from section definitions.
    
    Args:
        name: Template name
        description: Template description
        entity_def: Target entity type (e.g., "kahua_Contract.Contract")
        sections_json: JSON array of section definitions
        theme_json: Optional theme configuration as JSON
        category: Template category
        tags: Comma-separated tags
    
    Returns:
        Created template ID and definition
    
    Section types:
    - title: {kind: "title", text: "...", subtitle: "..."}
    - header: {kind: "header", text: "...", level: 2}
    - field_grid: {kind: "field_grid", fields: [{path: "...", label: "...", format: "text|currency|date|..."}], columns: 2}
    - data_table: {kind: "data_table", source: "Items", columns: [{key: "...", label: "...", format: "..."}]}
    - text: {kind: "text", content: "Text with {Placeholders}"}
    - divider: {kind: "divider"}
    - page_break: {kind: "page_break"}
    """
    try:
        # Parse sections
        sections_data = json.loads(sections_json)
        sections = []
        
        for idx, s in enumerate(sections_data):
            section = _parse_section_dict(s, idx)
            if section:
                sections.append(section)
        
        # Parse theme
        theme = ThemeDef()
        if theme_json:
            theme = ThemeDef.from_dict(json.loads(theme_json))
        
        # Create template
        template = WordTemplateDef(
            name=name,
            description=description,
            entity_def=entity_def,
            sections=sections,
            theme=theme,
            category=category,
            tags=tags.split(',') if tags else []
        )
        
        # Save
        registry = get_registry()
        template_id = registry.save(template)
        
        return {
            "status": "ok",
            "template_id": template_id,
            "template": template.to_dict(),
            "message": f"Template '{name}' created with {len(sections)} sections"
        }
    except Exception as e:
        log.error(f"Error creating template: {e}")
        return {"status": "error", "error": str(e)}


@function_tool
async def add_template_section(
    template_id: str,
    section_json: str,
    position: Optional[int] = None
) -> dict:
    """
    Add a section to an existing template.
    
    Args:
        template_id: Template to modify
        section_json: Section definition as JSON
        position: Insert position (appends if not specified)
    
    Returns:
        Updated template
    """
    try:
        registry = get_registry()
        template = registry.load(template_id)
        
        if not template:
            return {"status": "error", "error": f"Template '{template_id}' not found"}
        
        section_data = json.loads(section_json)
        section = _parse_section_dict(section_data, len(template.sections))
        
        if section:
            if position is not None and 0 <= position <= len(template.sections):
                template.sections.insert(position, section)
                # Reorder
                for i, s in enumerate(template.sections):
                    s.order = i
            else:
                section.order = len(template.sections)
                template.sections.append(section)
            
            registry.save(template)
            
            return {
                "status": "ok",
                "template_id": template_id,
                "section_count": len(template.sections),
                "message": f"Section added to template"
            }
        else:
            return {"status": "error", "error": "Invalid section definition"}
    except Exception as e:
        log.error(f"Error adding section: {e}")
        return {"status": "error", "error": str(e)}


@function_tool
async def update_template_theme(
    template_id: str,
    theme_json: str
) -> dict:
    """
    Update a template's theme/styling.
    
    Args:
        template_id: Template to modify
        theme_json: Theme configuration as JSON
    
    Returns:
        Updated template
    
    Theme options:
    - primary_color, secondary_color, accent_color: Hex colors
    - heading_font, body_font: Font names
    - title_size, heading1_size, heading2_size, body_size: Point sizes
    - table_header_bg, table_header_fg, table_stripe_bg: Table colors
    - orientation: "portrait" or "landscape"
    - margin_top, margin_bottom, margin_left, margin_right: Inches
    """
    try:
        registry = get_registry()
        template = registry.load(template_id)
        
        if not template:
            return {"status": "error", "error": f"Template '{template_id}' not found"}
        
        theme_data = json.loads(theme_json)
        
        # Merge with existing theme
        existing = template.theme.to_dict() if template.theme else {}
        existing.update(theme_data)
        template.theme = ThemeDef.from_dict(existing)
        
        registry.save(template)
        
        return {
            "status": "ok",
            "template_id": template_id,
            "theme": template.theme.to_dict(),
            "message": "Theme updated"
        }
    except Exception as e:
        log.error(f"Error updating theme: {e}")
        return {"status": "error", "error": str(e)}


# ============== Rendering Tools ==============

@function_tool
async def render_word_template(
    template_id: str,
    data_json: str,
    filename: Optional[str] = None
) -> dict:
    """
    Render a Word template with entity data.
    
    Args:
        template_id: Template ID to render
        data_json: Entity data as JSON string
        filename: Output filename (auto-generated if not provided)
    
    Returns:
        Path to generated document and base64-encoded bytes
    """
    try:
        import base64
        
        # Load template
        if template_id == "builtin-contract":
            template = get_contract_template()
        elif template_id == "builtin-rfi":
            template = get_rfi_template()
        else:
            registry = get_registry()
            template = registry.load(template_id)
        
        if not template:
            return {"status": "error", "error": f"Template '{template_id}' not found"}
        
        # Parse data
        data = json.loads(data_json)
        
        # Render
        path, doc_bytes = render_template(template, data, filename=filename)
        
        return {
            "status": "ok",
            "output_path": str(path),
            "filename": path.name,
            "size_bytes": len(doc_bytes),
            "document_base64": base64.b64encode(doc_bytes).decode('utf-8'),
            "message": f"Document rendered: {path.name}"
        }
    except Exception as e:
        log.error(f"Error rendering template: {e}")
        return {"status": "error", "error": str(e)}


@function_tool
async def quick_render_document(
    title: str,
    data_json: str,
    fields: Optional[str] = None,
    table_source: Optional[str] = None,
    table_columns: Optional[str] = None,
    filename: Optional[str] = None
) -> dict:
    """
    Quick render a simple document without creating a full template.
    
    Args:
        title: Document title
        data_json: Entity data as JSON string
        fields: Comma-separated field paths for summary grid
        table_source: Data path for table (e.g., "Items")
        table_columns: Comma-separated column keys for table
        filename: Output filename
    
    Returns:
        Path to generated document
    """
    try:
        import base64
        
        data = json.loads(data_json)
        field_list = [f.strip() for f in fields.split(',')] if fields else None
        column_list = [c.strip() for c in table_columns.split(',')] if table_columns else None
        
        path, doc_bytes = quick_render(
            title=title,
            data=data,
            fields=field_list,
            table_source=table_source,
            table_columns=column_list,
            filename=filename
        )
        
        return {
            "status": "ok",
            "output_path": str(path),
            "filename": path.name,
            "size_bytes": len(doc_bytes),
            "document_base64": base64.b64encode(doc_bytes).decode('utf-8'),
            "message": f"Document rendered: {path.name}"
        }
    except Exception as e:
        log.error(f"Error in quick render: {e}")
        return {"status": "error", "error": str(e)}


# ============== Helper Functions ==============

def _parse_section_dict(data: Dict[str, Any], default_order: int = 0) -> Optional[Section]:
    """Parse a section definition dict into a Section object."""
    kind_str = data.get("kind", data.get("type", "text"))
    
    try:
        kind = SectionKind(kind_str)
    except ValueError:
        log.warning(f"Unknown section kind: {kind_str}")
        return None
    
    order = data.get("order", default_order)
    condition = None
    if "condition" in data:
        condition = Condition.from_dict(data["condition"])
    
    section = Section(kind=kind, order=order, condition=condition)
    
    if kind == SectionKind.TITLE:
        section.title_config = TitleSection(
            text=data.get("text", ""),
            subtitle=data.get("subtitle")
        )
    
    elif kind == SectionKind.HEADER:
        section.header_config = HeaderSection(
            text=data.get("text", ""),
            level=data.get("level", 2)
        )
    
    elif kind == SectionKind.FIELD_GRID:
        fields = []
        for f in data.get("fields", []):
            if isinstance(f, dict):
                fields.append(FieldDef.from_dict(f))
            elif isinstance(f, str):
                # Just a path string
                fields.append(FieldDef(path=f))
        section.field_grid_config = FieldGridSection(
            fields=fields,
            columns=data.get("columns", 2),
            show_labels=data.get("show_labels", True),
            striped=data.get("striped", True)
        )
    
    elif kind == SectionKind.DATA_TABLE:
        columns = []
        for c in data.get("columns", []):
            if isinstance(c, dict):
                columns.append(ColumnDef.from_dict(c))
            elif isinstance(c, str):
                columns.append(ColumnDef(key=c, label=c))
        section.data_table_config = DataTableSection(
            source=data.get("source", ""),
            columns=columns,
            show_header=data.get("show_header", True),
            show_row_numbers=data.get("show_row_numbers", False),
            striped=data.get("striped", True),
            sort_by=data.get("sort_by"),
            sort_desc=data.get("sort_desc", False),
            max_rows=data.get("max_rows"),
            totals=data.get("totals"),
            empty_message=data.get("empty_message", "No items")
        )
    
    elif kind == SectionKind.TEXT:
        section.text_config = TextSection(content=data.get("content", ""))
    
    elif kind == SectionKind.IMAGE:
        section.image_config = ImageSection(
            source=data.get("source", "static"),
            path=data.get("path"),
            width=data.get("width"),
            height=data.get("height"),
            align=Alignment(data.get("align", "left")),
            caption=data.get("caption")
        )
    
    elif kind == SectionKind.SIGNATURE:
        section.signature_config = SignatureSection(
            lines=data.get("lines", []),
            columns=data.get("columns", 2),
            show_date=data.get("show_date", True)
        )
    
    elif kind == SectionKind.SPACER:
        section.spacer_config = SpacerSection(height=data.get("height", 12))
    
    # DIVIDER and PAGE_BREAK need no config
    
    return section


# ============== Export Tools List ==============

WORD_TEMPLATE_TOOLS = [
    list_word_templates,
    get_word_template,
    save_word_template,
    delete_word_template,
    duplicate_word_template,
    create_word_template,
    add_template_section,
    update_template_theme,
    render_word_template,
    quick_render_document,
]


def get_tool_definitions() -> List[Dict[str, Any]]:
    """Get OpenAI-format tool definitions for the Word template tools."""
    definitions = []
    
    for tool in WORD_TEMPLATE_TOOLS:
        # Extract from docstring
        doc = tool.__doc__ or ""
        lines = doc.strip().split('\n')
        description = lines[0] if lines else tool.__name__
        
        definitions.append({
            "type": "function",
            "function": {
                "name": tool.__name__,
                "description": description,
            }
        })
    
    return definitions
