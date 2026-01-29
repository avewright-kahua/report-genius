"""
Word Template Renderer
Renders WordTemplateDef definitions with entity data to Word documents.
"""

import io
import re
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List, Union
from datetime import datetime

from word_template_builder import (
    WordDocumentBuilder, DocumentTheme, PageMargins,
    FontStyle, Alignment, FieldFormat, Orientation,
    resolve_data_path, format_value, interpolate_template
)
from word_template_defs import (
    WordTemplateDef, Section, SectionKind, Condition,
    ThemeDef, FieldDef, ColumnDef,
    TitleSection, HeaderSection, FieldGridSection, DataTableSection,
    TextSection, ImageSection, SignatureSection, SpacerSection,
    TemplateRegistry, get_registry
)

log = logging.getLogger("word_template_renderer")

# Output directory
OUTPUTS_DIR = Path(__file__).parent / "reports"
OUTPUTS_DIR.mkdir(exist_ok=True)


def theme_def_to_document_theme(theme: ThemeDef) -> DocumentTheme:
    """Convert ThemeDef to DocumentTheme for builder."""
    return DocumentTheme(
        name=theme.name,
        primary_color=theme.primary_color,
        secondary_color=theme.secondary_color,
        accent_color=theme.accent_color,
        text_color=theme.text_color,
        muted_color=theme.muted_color,
        heading_font=theme.heading_font,
        body_font=theme.body_font,
        title_size=theme.title_size,
        heading1_size=theme.heading1_size,
        heading2_size=theme.heading2_size,
        heading3_size=theme.heading3_size,
        body_size=theme.body_size,
        small_size=theme.small_size,
        table_header_bg=theme.table_header_bg,
        table_header_fg=theme.table_header_fg,
        table_stripe_bg=theme.table_stripe_bg,
        table_border_color=theme.table_border_color,
        orientation=Orientation(theme.orientation.value) if theme.orientation else Orientation.PORTRAIT,
        margins=PageMargins(
            top=theme.margin_top,
            bottom=theme.margin_bottom,
            left=theme.margin_left,
            right=theme.margin_right,
        )
    )


class WordTemplateRenderer:
    """
    Renders Word documents from WordTemplateDef and entity data.
    
    Usage:
        renderer = WordTemplateRenderer()
        path, doc_bytes = renderer.render(template, data, filename="output.docx")
        
        # Or just get bytes
        doc_bytes = renderer.render_to_bytes(template, data)
    """
    
    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or OUTPUTS_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def render(
        self,
        template: WordTemplateDef,
        data: Dict[str, Any],
        filename: str = None
    ) -> Tuple[Path, bytes]:
        """
        Render template with data to Word document.
        
        Args:
            template: WordTemplateDef to render
            data: Entity data dictionary
            filename: Output filename (auto-generated if not provided)
        
        Returns:
            Tuple of (output path, document bytes)
        """
        doc_bytes = self.render_to_bytes(template, data)
        
        # Generate filename
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = re.sub(r'[^\w\-]', '_', template.name)[:30]
            filename = f"{safe_name}_{timestamp}.docx"
        elif not filename.endswith('.docx'):
            filename = f"{filename}.docx"
        
        output_path = self.output_dir / filename
        with open(output_path, 'wb') as f:
            f.write(doc_bytes)
        
        log.info(f"Rendered document: {output_path}")
        return output_path, doc_bytes
    
    def render_to_bytes(
        self,
        template: WordTemplateDef,
        data: Dict[str, Any]
    ) -> bytes:
        """Render template to bytes without saving to disk."""
        # Create builder with theme
        theme = theme_def_to_document_theme(template.theme) if template.theme else DocumentTheme()
        builder = WordDocumentBuilder(theme=theme)
        
        # Add header/footer
        if template.header_text or template.footer_text or template.show_page_numbers:
            builder.add_header_footer(
                header_text=interpolate_template(template.header_text, data) if template.header_text else None,
                footer_text=interpolate_template(template.footer_text, data) if template.footer_text else None,
                show_page_numbers=template.show_page_numbers
            )
        
        # Sort sections by order
        sections = sorted(template.sections, key=lambda s: s.order)
        
        # Render each section
        for section in sections:
            self._render_section(builder, section, data)
        
        return builder.save_to_bytes()
    
    def render_to_stream(
        self,
        template: WordTemplateDef,
        data: Dict[str, Any]
    ) -> io.BytesIO:
        """Render template to BytesIO stream."""
        doc_bytes = self.render_to_bytes(template, data)
        return io.BytesIO(doc_bytes)
    
    def _render_section(
        self,
        builder: WordDocumentBuilder,
        section: Section,
        data: Dict[str, Any]
    ):
        """Render a single section."""
        # Check condition
        if section.condition and not self._evaluate_condition(section.condition, data):
            return
        
        kind = section.kind
        
        if kind == SectionKind.TITLE:
            self._render_title(builder, section.title_config, data)
        
        elif kind == SectionKind.HEADER:
            self._render_header(builder, section.header_config, data)
        
        elif kind == SectionKind.FIELD_GRID:
            self._render_field_grid(builder, section.field_grid_config, data)
        
        elif kind == SectionKind.DATA_TABLE:
            self._render_data_table(builder, section.data_table_config, data)
        
        elif kind == SectionKind.TEXT:
            self._render_text(builder, section.text_config, data)
        
        elif kind == SectionKind.IMAGE:
            self._render_image(builder, section.image_config, data)
        
        elif kind == SectionKind.SIGNATURE:
            self._render_signature(builder, section.signature_config, data)
        
        elif kind == SectionKind.DIVIDER:
            builder.add_divider()
        
        elif kind == SectionKind.SPACER:
            height = section.spacer_config.height if section.spacer_config else 12
            builder.add_spacer(height)
        
        elif kind == SectionKind.PAGE_BREAK:
            builder.add_page_break()
    
    def _render_title(
        self,
        builder: WordDocumentBuilder,
        config: TitleSection,
        data: Dict[str, Any]
    ):
        """Render title section."""
        if not config:
            return
        
        title = interpolate_template(config.text, data)
        subtitle = interpolate_template(config.subtitle, data) if config.subtitle else None
        builder.add_title(title, subtitle)
    
    def _render_header(
        self,
        builder: WordDocumentBuilder,
        config: HeaderSection,
        data: Dict[str, Any]
    ):
        """Render section header."""
        if not config:
            return
        
        text = interpolate_template(config.text, data)
        builder.add_section_header(text, level=config.level)
    
    def _render_field_grid(
        self,
        builder: WordDocumentBuilder,
        config: FieldGridSection,
        data: Dict[str, Any]
    ):
        """Render field grid section."""
        if not config or not config.fields:
            return
        
        fields = []
        for field_def in config.fields:
            raw_value = resolve_data_path(data, field_def.path)
            fields.append({
                "label": field_def.label or self._path_to_label(field_def.path),
                "value": raw_value if raw_value is not None else field_def.default,
                "format": field_def.format,
                "format_options": field_def.format_options or {},
            })
        
        builder.add_field_grid(
            fields=fields,
            columns=config.columns,
            show_labels=config.show_labels,
            striped=config.striped
        )
    
    def _render_data_table(
        self,
        builder: WordDocumentBuilder,
        config: DataTableSection,
        data: Dict[str, Any]
    ):
        """Render data table section."""
        if not config or not config.columns:
            return
        
        # Get table data
        table_data = resolve_data_path(data, config.source)
        if not isinstance(table_data, list):
            table_data = [table_data] if table_data else []
        
        if not table_data:
            builder.add_text(config.empty_message)
            return
        
        # Apply sorting
        if config.sort_by:
            table_data = sorted(
                table_data,
                key=lambda x: resolve_data_path(x, config.sort_by) or "",
                reverse=config.sort_desc
            )
        
        # Apply row limit
        if config.max_rows:
            table_data = table_data[:config.max_rows]
        
        # Convert columns
        columns = []
        for col_def in config.columns:
            columns.append({
                "key": col_def.key,
                "label": col_def.label,
                "format": col_def.format,
                "format_options": col_def.format_options or {},
                "width": col_def.width,
                "align": col_def.align,
            })
        
        # Calculate totals if requested
        totals = None
        if config.totals:
            totals = {}
            for col_key in config.totals:
                total = 0
                for row in table_data:
                    val = resolve_data_path(row, col_key)
                    try:
                        total += float(val) if val else 0
                    except (ValueError, TypeError):
                        pass
                totals[col_key] = total
        
        builder.add_data_table(
            columns=columns,
            rows=table_data,
            show_header=config.show_header,
            show_row_numbers=config.show_row_numbers,
            striped=config.striped,
            totals=totals
        )
    
    def _render_text(
        self,
        builder: WordDocumentBuilder,
        config: TextSection,
        data: Dict[str, Any]
    ):
        """Render text section."""
        if not config:
            return
        
        content = interpolate_template(config.content, data)
        for para_text in content.split('\n'):
            if para_text.strip():
                builder.add_text(para_text.strip())
    
    def _render_image(
        self,
        builder: WordDocumentBuilder,
        config: ImageSection,
        data: Dict[str, Any]
    ):
        """Render image section."""
        if not config:
            return
        
        try:
            import base64
            
            image_source = None
            
            if config.source == "field" and config.path:
                img_value = resolve_data_path(data, config.path)
                if img_value and isinstance(img_value, str):
                    image_source = io.BytesIO(base64.b64decode(img_value))
            
            elif config.source in ("static", "logo") and config.path:
                image_source = config.path  # URL or file path
            
            if image_source:
                builder.add_image(
                    image_source,
                    width=config.width,
                    height=config.height,
                    alignment=config.align,
                    caption=interpolate_template(config.caption, data) if config.caption else None
                )
        except Exception as e:
            log.error(f"Failed to render image: {e}")
    
    def _render_signature(
        self,
        builder: WordDocumentBuilder,
        config: SignatureSection,
        data: Dict[str, Any]
    ):
        """Render signature block."""
        if not config:
            return
        
        # For now, add as text. Could enhance with actual signature line styling.
        for line in config.lines:
            label = line.get("label", "Signature")
            if "path" in line:
                value = resolve_data_path(data, line["path"])
                text = f"{label}: {value}" if value else label
            else:
                text = label
            builder.add_text(f"____________________\n{text}")
    
    def _evaluate_condition(self, condition: Condition, data: Dict[str, Any]) -> bool:
        """Evaluate a condition against data."""
        value = resolve_data_path(data, condition.field)
        op = condition.op
        compare_value = condition.value
        
        if op == "exists":
            return value is not None
        elif op == "not_empty":
            if value is None:
                return False
            if isinstance(value, (list, dict, str)):
                return len(value) > 0
            return True
        elif op == "eq":
            return value == compare_value
        elif op == "ne":
            return value != compare_value
        elif op == "gt":
            return value is not None and value > compare_value
        elif op == "lt":
            return value is not None and value < compare_value
        elif op == "gte":
            return value is not None and value >= compare_value
        elif op == "lte":
            return value is not None and value <= compare_value
        elif op == "contains":
            return compare_value in str(value) if value else False
        elif op == "in":
            return value in compare_value if compare_value else False
        
        return True
    
    def _path_to_label(self, path: str) -> str:
        """Convert field path to human-readable label."""
        name = path.split('.')[-1]
        # Insert space before capitals
        label = re.sub(r'(?<!^)(?=[A-Z])', ' ', name)
        return label


# ============== Convenience Functions ==============

def render_template(
    template: Union[WordTemplateDef, str],
    data: Dict[str, Any],
    output_dir: Path = None,
    filename: str = None
) -> Tuple[Path, bytes]:
    """
    Render a template to Word document.
    
    Args:
        template: WordTemplateDef or template ID string
        data: Entity data dictionary
        output_dir: Output directory (defaults to reports/)
        filename: Output filename
    
    Returns:
        Tuple of (output path, document bytes)
    """
    # Load template if string ID provided
    if isinstance(template, str):
        registry = get_registry()
        template = registry.load(template)
        if not template:
            raise ValueError(f"Template not found: {template}")
    
    renderer = WordTemplateRenderer(output_dir)
    return renderer.render(template, data, filename)


def render_template_to_bytes(
    template: Union[WordTemplateDef, str],
    data: Dict[str, Any]
) -> bytes:
    """
    Render a template to bytes.
    
    Args:
        template: WordTemplateDef or template ID string
        data: Entity data dictionary
    
    Returns:
        Document bytes
    """
    if isinstance(template, str):
        registry = get_registry()
        template = registry.load(template)
        if not template:
            raise ValueError(f"Template not found: {template}")
    
    renderer = WordTemplateRenderer()
    return renderer.render_to_bytes(template, data)


def render_builtin_contract(data: Dict[str, Any], filename: str = None) -> Tuple[Path, bytes]:
    """Render the built-in contract template."""
    from word_template_defs import get_contract_template
    template = get_contract_template()
    return render_template(template, data, filename=filename)


def render_builtin_rfi(data: Dict[str, Any], filename: str = None) -> Tuple[Path, bytes]:
    """Render the built-in RFI template."""
    from word_template_defs import get_rfi_template
    template = get_rfi_template()
    return render_template(template, data, filename=filename)


# ============== Template from Data Helper ==============

def quick_render(
    title: str,
    data: Dict[str, Any],
    fields: List[str] = None,
    table_source: str = None,
    table_columns: List[str] = None,
    filename: str = None
) -> Tuple[Path, bytes]:
    """
    Quick render a simple document without defining a full template.
    
    Args:
        title: Document title
        data: Entity data
        fields: List of field paths to include in summary grid
        table_source: Data path for table (e.g., "Items")
        table_columns: Columns for table
        filename: Output filename
    
    Returns:
        Tuple of (output path, document bytes)
    """
    from word_template_defs import (
        WordTemplateDef, create_title_section, create_field_grid_section,
        create_table_section, create_field, create_column, FieldFormat
    )
    
    sections = [create_title_section(title, order=0)]
    order = 1
    
    # Add field grid if fields provided
    if fields:
        field_defs = []
        for f in fields:
            # Auto-detect format from field name
            fmt = FieldFormat.TEXT
            lower_f = f.lower()
            if any(kw in lower_f for kw in ['amount', 'value', 'cost', 'price', 'total']):
                fmt = FieldFormat.CURRENCY
            elif any(kw in lower_f for kw in ['date', 'created', 'updated']):
                fmt = FieldFormat.DATE
            elif any(kw in lower_f for kw in ['percent', 'rate']):
                fmt = FieldFormat.PERCENT
            
            label = re.sub(r'(?<!^)(?=[A-Z])', ' ', f.split('.')[-1])
            field_defs.append(create_field(f, label, fmt))
        
        sections.append(create_field_grid_section(field_defs, columns=2, order=order))
        order += 1
    
    # Add table if table source provided
    if table_source and table_columns:
        col_defs = []
        for c in table_columns:
            fmt = FieldFormat.TEXT
            lower_c = c.lower()
            if any(kw in lower_c for kw in ['amount', 'value', 'cost', 'price', 'total']):
                fmt = FieldFormat.CURRENCY
            label = re.sub(r'(?<!^)(?=[A-Z])', ' ', c.split('.')[-1])
            col_defs.append(create_column(c, label, fmt))
        
        sections.append(create_table_section(table_source, col_defs, order=order))
    
    template = WordTemplateDef(
        name=title,
        sections=sections
    )
    
    return render_template(template, data, filename=filename)
