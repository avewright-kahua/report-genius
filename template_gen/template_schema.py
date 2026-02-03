"""
Template Schema - Pydantic models defining the portable view template structure.

This module provides type-safe definitions for the JSON template format,
enabling validation, serialization, and programmatic manipulation of templates.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union
from uuid import uuid4

from pydantic import BaseModel, Field


class SectionType(str, Enum):
    """Types of sections that can appear in a template."""
    
    HEADER = "header"       # Title/identity section at top
    DETAIL = "detail"       # Key-value pairs in grid layout
    TEXT = "text"           # Long-form text content
    TABLE = "table"         # Tabular data from collections
    IMAGE = "image"         # Static or dynamic images
    DIVIDER = "divider"     # Visual separator
    SPACER = "spacer"       # Vertical whitespace
    LIST = "list"           # Bulleted or numbered list


class FieldFormat(str, Enum):
    """Format types for field values matching Kahua token types."""
    
    TEXT = "text"              # [Attribute(Path)]
    CURRENCY = "currency"       # [Currency(Source=Attribute,Path=...,Format="C2")]
    NUMBER = "number"           # [Number(Source=Attribute,Path=...,Format="N0")]
    DECIMAL = "decimal"         # [Number(Source=Attribute,Path=...,Format="F2")]
    PERCENT = "percent"         # [Number(Source=Attribute,Path=...,Format="P1")]
    DATE = "date"               # [Date(Source=Attribute,Path=...,Format="d")]
    DATETIME = "datetime"       # [Date(Source=Attribute,Path=...,Format="g")]
    BOOLEAN = "boolean"         # [Boolean(Source=Attribute,Path=...,TrueValue="Yes",FalseValue="No")]
    RICH_TEXT = "rich_text"     # [RichText(Source=Attribute,Path=...)]
    PHONE = "phone"             # [Attribute(Path)]
    EMAIL = "email"             # [Attribute(Path)]
    URL = "url"                 # [Attribute(Path)]
    IMAGE = "image"             # [Image(Path=...)]


class Alignment(str, Enum):
    """Text/content alignment options."""
    
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


class LayoutType(str, Enum):
    """Layout options for detail sections."""
    
    GRID = "grid"           # Multi-column grid
    HORIZONTAL = "horizontal"  # Single row
    VERTICAL = "vertical"   # Single column stacked


class ConditionOperator(str, Enum):
    """Operators for conditional rendering."""
    
    NOT_EMPTY = "not_empty"
    EMPTY = "empty"
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    CONTAINS = "contains"


# ============================================================================
# Field Definitions
# ============================================================================

class FormatOptions(BaseModel):
    """Options for field formatting."""
    
    decimals: Optional[int] = None
    format: Optional[str] = None  # Date format string
    prefix: Optional[str] = None  # e.g., "$"
    suffix: Optional[str] = None  # e.g., "%"
    default: Optional[str] = None  # Default if empty
    thousand_separator: bool = True


class FieldDef(BaseModel):
    """Definition of a single field in the template."""
    
    path: str  # Dot-notation path to field (e.g., "ContractorCompany.ShortLabel")
    label: Optional[str] = None  # Display label (auto-generated if not provided)
    format: FieldFormat = FieldFormat.TEXT
    format_options: Optional[FormatOptions] = None
    alignment: Alignment = Alignment.LEFT


class Condition(BaseModel):
    """Conditional rendering rule."""
    
    field: str  # Field path to check
    op: ConditionOperator = ConditionOperator.NOT_EMPTY
    value: Optional[Any] = None  # Value for comparison operators


# ============================================================================
# Section Configurations
# ============================================================================

class HeaderConfig(BaseModel):
    """Configuration for header sections."""
    
    title_template: str = "{Number}"  # Template string using {field} placeholders
    subtitle_template: Optional[str] = None
    fields: List[FieldDef] = Field(default_factory=list)  # Additional header fields
    layout: LayoutType = LayoutType.HORIZONTAL
    show_labels: bool = False
    show_logo: bool = False  # Include company/project logo
    logo_type: str = "company"  # "company" or "project"
    logo_position: str = "left"  # "left" or "right"
    
    # Static title (literal text, not a placeholder)
    static_title: Optional[str] = None  # If set, displayed as literal text before/above placeholders
    
    # Title styling overrides
    title_font: Optional[str] = None      # Font family (e.g., "Comic Sans MS", "Arial Black")
    title_size: Optional[int] = None      # Font size in points (e.g., 28)
    title_color: Optional[str] = None     # Hex color (e.g., "#0000FF" for blue)
    title_bold: bool = True               # Whether title is bold
    title_alignment: Alignment = Alignment.LEFT


class DetailConfig(BaseModel):
    """Configuration for detail (key-value) sections."""
    
    fields: List[FieldDef]
    layout: LayoutType = LayoutType.GRID
    columns: int = 2
    show_labels: bool = True
    label_width: Optional[int] = None  # Percentage


class TextConfig(BaseModel):
    """Configuration for text block sections."""
    
    content: str  # Template string with {field} placeholders
    style: Optional[str] = None  # bold, italic, etc.
    hyperlinks: List["HyperlinkDef"] = Field(default_factory=list)  # Inline hyperlinks


class TableColumn(BaseModel):
    """Definition of a table column."""
    
    field: FieldDef
    width: Optional[int] = None  # Percentage or character width
    alignment: Alignment = Alignment.LEFT
    min_width: Optional[int] = None
    max_width: Optional[int] = None


class TableConfig(BaseModel):
    """Configuration for table sections."""
    
    source: str  # Path to collection field (e.g., "Items")
    columns: List[TableColumn]
    show_header: bool = True
    max_rows: Optional[int] = None
    empty_message: Optional[str] = None
    show_subtotals: bool = False
    subtotal_fields: List[str] = Field(default_factory=list)
    row_condition: Optional[Condition] = None  # Filter rows


class ImageConfig(BaseModel):
    """Configuration for image sections."""
    
    source: Literal["static", "field"] = "static"
    url: Optional[str] = None  # For static images
    field_path: Optional[str] = None  # For dynamic images
    width: Optional[float] = None  # Inches
    height: Optional[float] = None  # Inches
    alignment: Alignment = Alignment.LEFT
    caption: Optional[str] = None


class DividerConfig(BaseModel):
    """Configuration for divider sections."""
    
    style: Literal["solid", "dashed", "dotted", "double"] = "solid"
    thickness: float = 1.0  # Points
    color: Optional[str] = None  # Hex color


class SpacerConfig(BaseModel):
    """Configuration for spacer sections."""
    
    height: float = 0.25  # Inches


class ListConfig(BaseModel):
    """Configuration for list sections (bulleted or numbered)."""
    
    list_type: Literal["bullet", "number"] = "bullet"
    items: List[str] = Field(default_factory=list)  # Static items or {field} templates
    source: Optional[str] = None  # Path to collection for dynamic lists
    item_field: Optional[str] = None  # Field to display from each item in collection
    indent_level: int = 0  # Nesting level (0 = top level)


class PageHeaderFooterConfig(BaseModel):
    """Configuration for page headers and footers."""
    
    left_text: Optional[str] = None    # Text/placeholder for left side
    center_text: Optional[str] = None  # Text/placeholder for center
    right_text: Optional[str] = None   # Text/placeholder for right side
    include_page_number: bool = False  # Add page number
    page_number_format: str = "Page {page} of {total}"  # Format for page numbers
    font_size: int = 9
    show_on_first_page: bool = True


class HyperlinkDef(BaseModel):
    """Definition for a hyperlink in text content."""
    
    text: str                          # Display text
    url: str                           # URL (can include Kahua placeholder like {WebUrl})
    tooltip: Optional[str] = None      # Optional hover tooltip


# ============================================================================
# Section Definition
# ============================================================================

class Section(BaseModel):
    """A single section in the template."""
    
    type: SectionType
    title: Optional[str] = None
    order: int = 0
    condition: Optional[Condition] = None  # When to show this section
    
    # Type-specific configs (only one should be set based on type)
    header_config: Optional[HeaderConfig] = None
    detail_config: Optional[DetailConfig] = None
    text_config: Optional[TextConfig] = None
    table_config: Optional[TableConfig] = None
    image_config: Optional[ImageConfig] = None
    divider_config: Optional[DividerConfig] = None
    spacer_config: Optional[SpacerConfig] = None
    list_config: Optional[ListConfig] = None
    
    def get_config(self) -> Optional[BaseModel]:
        """Get the active configuration based on section type."""
        config_map = {
            SectionType.HEADER: self.header_config,
            SectionType.DETAIL: self.detail_config,
            SectionType.TEXT: self.text_config,
            SectionType.TABLE: self.table_config,
            SectionType.IMAGE: self.image_config,
            SectionType.DIVIDER: self.divider_config,
            SectionType.SPACER: self.spacer_config,
            SectionType.LIST: self.list_config,
        }
        return config_map.get(self.type)


# ============================================================================
# Layout & Style
# ============================================================================

class LayoutConfig(BaseModel):
    """Page layout configuration."""
    
    orientation: Literal["portrait", "landscape"] = "portrait"
    margin_top: float = 0.75  # Inches
    margin_bottom: float = 0.75
    margin_left: float = 0.75
    margin_right: float = 0.75
    page_size: Literal["letter", "legal", "a4"] = "letter"
    columns: int = 1  # Number of content columns
    
    # Page header/footer
    page_header: Optional[PageHeaderFooterConfig] = None
    page_footer: Optional[PageHeaderFooterConfig] = None


class StyleConfig(BaseModel):
    """Visual styling configuration."""
    
    # Colors
    primary_color: str = "#0f172a"  # Slate 900
    secondary_color: str = "#0369a1"  # Sky 700
    accent_color: str = "#059669"  # Emerald 600
    text_color: str = "#1e293b"  # Slate 800
    muted_color: str = "#64748b"  # Slate 500
    
    # Fonts
    font_family: str = "Calibri"
    heading_font: str = "Calibri Light"
    mono_font: str = "Consolas"
    
    # Sizes
    title_size: int = 18
    heading_size: int = 12
    body_size: int = 10
    small_size: int = 8
    
    # Table styling
    table_header_bg: str = "#0f172a"
    table_header_fg: str = "#ffffff"
    table_alt_row_bg: str = "#f8fafc"  # Slate 50
    table_border_color: str = "#e2e8f0"  # Slate 200
    
    # Spacing
    section_spacing: float = 0.25  # Inches between sections


# ============================================================================
# Template Definition
# ============================================================================

class PortableViewTemplate(BaseModel):
    """Complete portable view template definition."""
    
    id: str = Field(default_factory=lambda: f"pv-{uuid4().hex[:8]}")
    name: str
    description: Optional[str] = None
    version: str = "1.0"
    
    # Target entity
    entity_def: str  # Kahua entity definition path
    
    # Layout and style
    layout: LayoutConfig = Field(default_factory=LayoutConfig)
    style: StyleConfig = Field(default_factory=StyleConfig)
    
    # Content sections
    sections: List[Section] = Field(default_factory=list)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    source_type: Literal["manual", "generated", "imported"] = "generated"
    
    model_config = {
        "json_encoders": {datetime: lambda v: v.isoformat()}
    }
    
    def get_sections_ordered(self) -> List[Section]:
        """Get sections sorted by order."""
        return sorted(self.sections, key=lambda s: s.order)
    
    def add_section(self, section: Section) -> None:
        """Add a section, auto-assigning order if needed."""
        if section.order == 0 and self.sections:
            section.order = max(s.order for s in self.sections) + 1
        self.sections.append(section)
        self.updated_at = datetime.now()
    
    def remove_section(self, index: int) -> Optional[Section]:
        """Remove section by index."""
        if 0 <= index < len(self.sections):
            removed = self.sections.pop(index)
            self.updated_at = datetime.now()
            return removed
        return None
    
    def reorder_sections(self, new_order: List[int]) -> None:
        """Reorder sections by specifying new index positions."""
        if len(new_order) != len(self.sections):
            raise ValueError("new_order must have same length as sections")
        self.sections = [self.sections[i] for i in new_order]
        for i, section in enumerate(self.sections):
            section.order = i
        self.updated_at = datetime.now()


# ============================================================================
# Builder Helpers
# ============================================================================

def create_header_section(
    title_template: str = "{Number}",
    subtitle_template: Optional[str] = None,
    order: int = 0,
) -> Section:
    """Create a header section."""
    return Section(
        type=SectionType.HEADER,
        order=order,
        header_config=HeaderConfig(
            title_template=title_template,
            subtitle_template=subtitle_template,
        ),
    )


def create_detail_section(
    fields: List[Dict[str, Any]],
    title: Optional[str] = None,
    columns: int = 2,
    order: int = 0,
    condition: Optional[Condition] = None,
) -> Section:
    """Create a detail (key-value) section."""
    field_defs = [
        FieldDef(
            path=f["path"],
            label=f.get("label"),
            format=FieldFormat(f.get("format", "text")),
            format_options=FormatOptions(**f["format_options"]) if f.get("format_options") else None,
        )
        for f in fields
    ]
    return Section(
        type=SectionType.DETAIL,
        title=title,
        order=order,
        condition=condition,
        detail_config=DetailConfig(
            fields=field_defs,
            columns=columns,
        ),
    )


def create_text_section(
    content: str,
    title: Optional[str] = None,
    order: int = 0,
    condition_field: Optional[str] = None,
) -> Section:
    """Create a text block section."""
    condition = None
    if condition_field:
        condition = Condition(field=condition_field, op=ConditionOperator.NOT_EMPTY)
    
    return Section(
        type=SectionType.TEXT,
        title=title,
        order=order,
        condition=condition,
        text_config=TextConfig(content=content),
    )


def create_table_section(
    source: str,
    columns: List[Dict[str, Any]],
    title: Optional[str] = None,
    order: int = 0,
    show_subtotals: bool = False,
    subtotal_fields: Optional[List[str]] = None,
) -> Section:
    """Create a table section."""
    table_columns = [
        TableColumn(
            field=FieldDef(
                path=c["path"],
                label=c.get("label"),
                format=FieldFormat(c.get("format", "text")),
            ),
            width=c.get("width"),
            alignment=Alignment(c.get("alignment", "left")),
        )
        for c in columns
    ]
    
    return Section(
        type=SectionType.TABLE,
        title=title,
        order=order,
        condition=Condition(field=source, op=ConditionOperator.NOT_EMPTY),
        table_config=TableConfig(
            source=source,
            columns=table_columns,
            show_subtotals=show_subtotals,
            subtotal_fields=subtotal_fields or [],
        ),
    )


def create_divider_section(order: int = 0) -> Section:
    """Create a divider section."""
    return Section(
        type=SectionType.DIVIDER,
        order=order,
        divider_config=DividerConfig(),
    )
