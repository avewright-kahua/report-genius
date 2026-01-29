"""
Template Renderer - Converts templates + entity data to output formats.

This module takes a PortableViewTemplate and entity data, then renders
to Markdown (for preview) or Word document (for export).
"""

from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union

from template_schema import (
    Alignment,
    Condition,
    ConditionOperator,
    DetailConfig,
    FieldDef,
    FieldFormat,
    HeaderConfig,
    PortableViewTemplate,
    Section,
    SectionType,
    TableColumn,
    TableConfig,
    TextConfig,
)


def _resolve_path(data: Dict[str, Any], path: str) -> Any:
    """Resolve a dot-notation path to a value in nested data.
    
    Args:
        data: The entity data dictionary
        path: Dot-notation path like "ContractorCompany.ShortLabel"
    
    Returns:
        The resolved value or None if not found
    """
    if not path or not data:
        return None
    
    parts = path.split(".")
    current = data
    
    for part in parts:
        if current is None:
            return None
        if isinstance(current, dict):
            # Try exact match, then PascalCase, then snake_case
            if part in current:
                current = current[part]
            elif part.lower() in {k.lower() for k in current}:
                # Case-insensitive match
                for k, v in current.items():
                    if k.lower() == part.lower():
                        current = v
                        break
            else:
                return None
        else:
            # Try attribute access for objects
            if hasattr(current, part):
                current = getattr(current, part)
            else:
                return None
    
    return current


def _format_value(
    value: Any,
    format_type: FieldFormat,
    format_options: Optional[Dict[str, Any]] = None,
) -> str:
    """Format a value according to its format specification."""
    if value is None:
        return format_options.get("default", "") if format_options else ""
    
    options = format_options or {}
    
    if format_type == FieldFormat.CURRENCY:
        try:
            num = Decimal(str(value))
            decimals = options.get("decimals", 2)
            prefix = options.get("prefix") or "$"
            formatted = f"{num:,.{decimals}f}"
            return f"{prefix}{formatted}"
        except (ValueError, TypeError):
            return str(value)
    
    if format_type == FieldFormat.NUMBER:
        try:
            num = float(value)
            if num == int(num):
                return f"{int(num):,}"
            return f"{num:,.2f}"
        except (ValueError, TypeError):
            return str(value)
    
    if format_type == FieldFormat.DECIMAL:
        try:
            num = Decimal(str(value))
            decimals = options.get("decimals", 2)
            return f"{num:.{decimals}f}"
        except (ValueError, TypeError):
            return str(value)
    
    if format_type == FieldFormat.PERCENT:
        try:
            num = float(value)
            suffix = options.get("suffix", "%")
            return f"{num:.1f}{suffix}"
        except (ValueError, TypeError):
            return str(value)
    
    if format_type == FieldFormat.DATE:
        if isinstance(value, (date, datetime)):
            fmt = options.get("format", "%b %d, %Y")
            # Convert from moment.js style to Python strftime if needed
            fmt = fmt.replace("MMM", "%b").replace("MM", "%m")
            fmt = fmt.replace("YYYY", "%Y").replace("DD", "%d").replace("D", "%-d")
            return value.strftime(fmt)
        return str(value)
    
    if format_type == FieldFormat.DATETIME:
        if isinstance(value, datetime):
            fmt = options.get("format", "%b %d, %Y %I:%M %p")
            return value.strftime(fmt)
        return str(value)
    
    if format_type == FieldFormat.BOOLEAN:
        if isinstance(value, bool):
            return "Yes" if value else "No"
        return str(value)
    
    # Default: text
    return str(value) if value else ""


def _evaluate_condition(data: Dict[str, Any], condition: Optional[Condition]) -> bool:
    """Evaluate a condition against entity data."""
    if condition is None:
        return True
    
    value = _resolve_path(data, condition.field)
    
    if condition.op == ConditionOperator.NOT_EMPTY:
        if isinstance(value, (list, dict)):
            return bool(value)
        return value is not None and str(value).strip() != ""
    
    if condition.op == ConditionOperator.EMPTY:
        if isinstance(value, (list, dict)):
            return not value
        return value is None or str(value).strip() == ""
    
    if condition.op == ConditionOperator.EQUALS:
        return value == condition.value
    
    if condition.op == ConditionOperator.NOT_EQUALS:
        return value != condition.value
    
    if condition.op == ConditionOperator.GREATER_THAN:
        try:
            return float(value) > float(condition.value)
        except (ValueError, TypeError):
            return False
    
    if condition.op == ConditionOperator.LESS_THAN:
        try:
            return float(value) < float(condition.value)
        except (ValueError, TypeError):
            return False
    
    if condition.op == ConditionOperator.CONTAINS:
        return str(condition.value).lower() in str(value).lower()
    
    return True


def _interpolate_template(template_str: str, data: Dict[str, Any]) -> str:
    """Replace {field} placeholders with values from data."""
    def replace(match: re.Match) -> str:
        path = match.group(1)
        value = _resolve_path(data, path)
        return str(value) if value is not None else ""
    
    return re.sub(r"\{([^}]+)\}", replace, template_str)


def _render_field_value(field: FieldDef, data: Dict[str, Any]) -> str:
    """Render a single field value."""
    value = _resolve_path(data, field.path)
    options = field.format_options.model_dump() if field.format_options else {}
    return _format_value(value, field.format, options)


# ============================================================================
# Markdown Renderer
# ============================================================================

class MarkdownRenderer:
    """Renders templates to Markdown format."""
    
    def __init__(self, template: PortableViewTemplate):
        self.template = template
    
    def render(self, data: Dict[str, Any]) -> str:
        """Render the template with entity data to Markdown."""
        lines: List[str] = []
        
        for section in self.template.get_sections_ordered():
            # Check condition
            if not _evaluate_condition(data, section.condition):
                continue
            
            section_md = self._render_section(section, data)
            if section_md:
                lines.append(section_md)
        
        # Add footer
        lines.append("")
        lines.append("---")
        lines.append(f"*Generated {datetime.now().strftime('%b %d, %Y %I:%M %p')}*")
        
        return "\n".join(lines)
    
    def _render_section(self, section: Section, data: Dict[str, Any]) -> str:
        """Render a single section."""
        if section.type == SectionType.HEADER:
            return self._render_header(section, data)
        if section.type == SectionType.DETAIL:
            return self._render_detail(section, data)
        if section.type == SectionType.TEXT:
            return self._render_text(section, data)
        if section.type == SectionType.TABLE:
            return self._render_table(section, data)
        if section.type == SectionType.DIVIDER:
            return "\n---\n"
        if section.type == SectionType.SPACER:
            return "\n"
        return ""
    
    def _render_header(self, section: Section, data: Dict[str, Any]) -> str:
        """Render header section."""
        config = section.header_config
        if not config:
            return ""
        
        lines = []
        
        # Title
        title = _interpolate_template(config.title_template, data)
        lines.append(f"# {title}")
        
        # Subtitle
        if config.subtitle_template:
            subtitle = _interpolate_template(config.subtitle_template, data)
            if subtitle:
                lines.append(f"**{subtitle}**")
        
        lines.append("")
        return "\n".join(lines)
    
    def _render_detail(self, section: Section, data: Dict[str, Any]) -> str:
        """Render detail (key-value) section."""
        config = section.detail_config
        if not config or not config.fields:
            return ""
        
        lines = []
        
        # Section title
        if section.title:
            lines.append(f"## {section.title}")
            lines.append("")
        
        # Render as table for better formatting
        lines.append("| | |")
        lines.append("|:--|:--|")
        
        for field in config.fields:
            value = _render_field_value(field, data)
            if value or not field.format_options or not field.format_options.default:
                label = field.label or field.path
                lines.append(f"| **{label}** | {value} |")
        
        lines.append("")
        return "\n".join(lines)
    
    def _render_text(self, section: Section, data: Dict[str, Any]) -> str:
        """Render text block section."""
        config = section.text_config
        if not config:
            return ""
        
        content = _interpolate_template(config.content, data)
        if not content.strip():
            return ""
        
        lines = []
        
        if section.title:
            lines.append(f"## {section.title}")
            lines.append("")
        
        lines.append(content)
        lines.append("")
        
        return "\n".join(lines)
    
    def _render_table(self, section: Section, data: Dict[str, Any]) -> str:
        """Render table section."""
        config = section.table_config
        if not config:
            return ""
        
        # Get collection data
        rows = _resolve_path(data, config.source)
        if not rows or not isinstance(rows, list):
            if config.empty_message:
                return f"*{config.empty_message}*\n"
            return ""
        
        # Apply row limit
        if config.max_rows:
            rows = rows[:config.max_rows]
        
        lines = []
        
        # Section title
        if section.title:
            lines.append(f"## {section.title}")
            lines.append("")
        
        # Header row
        if config.show_header:
            headers = [col.field.label or col.field.path for col in config.columns]
            lines.append("| " + " | ".join(headers) + " |")
            
            # Alignment row
            alignments = []
            for col in config.columns:
                if col.alignment == Alignment.RIGHT:
                    alignments.append("--:")
                elif col.alignment == Alignment.CENTER:
                    alignments.append(":-:")
                else:
                    alignments.append(":--")
            lines.append("| " + " | ".join(alignments) + " |")
        
        # Data rows
        subtotals: Dict[str, Decimal] = {f: Decimal(0) for f in config.subtotal_fields}
        
        for row in rows:
            cells = []
            for col in config.columns:
                value = _resolve_path(row, col.field.path)
                formatted = _format_value(
                    value,
                    col.field.format,
                    col.field.format_options.model_dump() if col.field.format_options else {},
                )
                cells.append(formatted)
                
                # Track subtotals
                if col.field.path in subtotals and value is not None:
                    try:
                        subtotals[col.field.path] += Decimal(str(value))
                    except (ValueError, TypeError):
                        pass
            
            lines.append("| " + " | ".join(cells) + " |")
        
        # Subtotals row
        if config.show_subtotals and any(subtotals.values()):
            cells = []
            for col in config.columns:
                if col.field.path in subtotals:
                    formatted = _format_value(
                        subtotals[col.field.path],
                        col.field.format,
                        col.field.format_options.model_dump() if col.field.format_options else {},
                    )
                    cells.append(f"**{formatted}**")
                else:
                    cells.append("")
            cells[0] = "**Total**" if cells[0] == "" else cells[0]
            lines.append("| " + " | ".join(cells) + " |")
        
        lines.append("")
        return "\n".join(lines)


def render_to_markdown(template: PortableViewTemplate, data: Dict[str, Any]) -> str:
    """Convenience function to render template to Markdown."""
    renderer = MarkdownRenderer(template)
    return renderer.render(data)


# ============================================================================
# Preview with Sample Data
# ============================================================================

def generate_sample_data(template: PortableViewTemplate) -> Dict[str, Any]:
    """Generate sample data for template preview.
    
    Creates placeholder values based on field definitions.
    """
    sample: Dict[str, Any] = {}
    
    for section in template.sections:
        if section.type == SectionType.HEADER and section.header_config:
            # Extract fields from title template
            for match in re.finditer(r"\{([^}]+)\}", section.header_config.title_template):
                path = match.group(1)
                _set_sample_value(sample, path, f"SAMPLE-{path.split('.')[-1].upper()}")
            if section.header_config.subtitle_template:
                for match in re.finditer(r"\{([^}]+)\}", section.header_config.subtitle_template):
                    path = match.group(1)
                    _set_sample_value(sample, path, f"Sample {path.split('.')[-1]}")
        
        elif section.type == SectionType.DETAIL and section.detail_config:
            for field in section.detail_config.fields:
                value = _get_sample_for_format(field.format, field.path)
                _set_sample_value(sample, field.path, value)
        
        elif section.type == SectionType.TEXT and section.text_config:
            for match in re.finditer(r"\{([^}]+)\}", section.text_config.content):
                path = match.group(1)
                _set_sample_value(sample, path, f"Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.")
        
        elif section.type == SectionType.TABLE and section.table_config:
            rows = []
            for i in range(3):
                row = {}
                for col in section.table_config.columns:
                    value = _get_sample_for_format(col.field.format, col.field.path, i + 1)
                    parts = col.field.path.split(".")
                    current = row
                    for part in parts[:-1]:
                        if part not in current:
                            current[part] = {}
                        current = current[part]
                    current[parts[-1]] = value
                rows.append(row)
            _set_sample_value(sample, section.table_config.source, rows)
    
    return sample


def _set_sample_value(data: Dict[str, Any], path: str, value: Any) -> None:
    """Set a value at a dot-notation path in a dict."""
    parts = path.split(".")
    current = data
    for part in parts[:-1]:
        if part not in current:
            current[part] = {}
        current = current[part]
    current[parts[-1]] = value


def _get_sample_for_format(format_type: FieldFormat, path: str, index: int = 1) -> Any:
    """Generate appropriate sample value for a format type."""
    name = path.split(".")[-1].lower()
    
    if format_type == FieldFormat.CURRENCY:
        return Decimal("12500.00") * index
    if format_type == FieldFormat.NUMBER:
        return 100 * index
    if format_type == FieldFormat.DECIMAL:
        return Decimal("3.14") * index
    if format_type == FieldFormat.PERCENT:
        return 25.5 * index
    if format_type == FieldFormat.DATE:
        return date(2026, 1, 15 + index)
    if format_type == FieldFormat.DATETIME:
        return datetime(2026, 1, 15 + index, 10, 30)
    if format_type == FieldFormat.BOOLEAN:
        return index % 2 == 1
    
    # Text - use path name as hint
    if "number" in name or "id" in name:
        return f"{name.upper()[:3]}-{1000 + index}"
    if "status" in name:
        return ["Draft", "Pending", "Approved"][index % 3]
    if "description" in name or "name" in name:
        return f"Sample {name} {index}"
    
    return f"Sample {name}"


# ============================================================================
# Demo
# ============================================================================

if __name__ == "__main__":
    import json
    from pathlib import Path
    from template_generator import generate_template
    from schema_introspector import get_available_schemas
    
    schemas = get_available_schemas()
    
    for name, schema in schemas.items():
        print(f"\n{'='*60}")
        print(f"Preview: {schema.name}")
        print(f"{'='*60}")
        
        template = generate_template(schema)
        sample = generate_sample_data(template)
        markdown = render_to_markdown(template, sample)
        
        print(markdown)
        
        # Save preview
        output_path = Path("pv_templates/saved") / f"preview-{name}.md"
        with open(output_path, "w") as f:
            f.write(markdown)
        print(f"\nSaved preview: {output_path}")
