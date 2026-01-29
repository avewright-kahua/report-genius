"""
Portable View Template Schema
Defines the JSON structure for reusable report templates that work with Kahua API data.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any, Literal
from enum import Enum
import json


class FieldFormat(str, Enum):
    """Data formatting options for template fields."""
    TEXT = "text"
    NUMBER = "number"
    CURRENCY = "currency"
    DATE = "date"
    DATETIME = "datetime"
    PERCENT = "percent"
    BOOLEAN = "boolean"
    RICH_TEXT = "rich_text"
    IMAGE = "image"
    URL = "url"


class SectionType(str, Enum):
    """Types of sections in a template."""
    HEADER = "header"           # Top of document, entity-level fields
    DETAIL = "detail"           # Key-value pairs, form-like
    TABLE = "table"             # Repeating rows from child entities
    TEXT = "text"               # Static or dynamic text blocks
    IMAGE = "image"             # Logo, photos, attachments
    CHART = "chart"             # Visualizations
    SIGNATURE = "signature"     # Signature blocks
    FOOTER = "footer"           # Page footer
    PAGE_BREAK = "page_break"   # Force new page
    GROUPED_TABLE = "grouped_table"  # Table with grouping/subtotals


class Orientation(str, Enum):
    PORTRAIT = "portrait"
    LANDSCAPE = "landscape"


class Alignment(str, Enum):
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


@dataclass
class FieldMapping:
    """Maps a template placeholder to an entity field path."""
    path: str                           # Dot-notation path: "Status.Name", "Items[0].Amount"
    label: Optional[str] = None         # Display label
    format: FieldFormat = FieldFormat.TEXT
    format_options: Optional[Dict[str, Any]] = None  # e.g., {"decimals": 2, "prefix": "$"}
    default_value: Optional[str] = None  # Fallback if field is empty
    condition: Optional[Dict[str, Any]] = None  # Show only if condition met
    transform: Optional[str] = None      # Optional transformation: "uppercase", "sum", etc.


@dataclass
class ColumnDef:
    """Column definition for table sections."""
    field: FieldMapping
    width: Optional[float] = None       # Width in inches or percentage
    alignment: Alignment = Alignment.LEFT
    header_style: Optional[Dict[str, Any]] = None
    cell_style: Optional[Dict[str, Any]] = None


@dataclass 
class TableSection:
    """Configuration for a table section."""
    source: str                         # Path to child collection: "Items", "References"
    entity_def: Optional[str] = None    # Entity def of items if known
    columns: List[ColumnDef] = field(default_factory=list)
    show_header: bool = True
    show_row_numbers: bool = False
    sort_by: Optional[str] = None
    sort_direction: str = "asc"
    filter_condition: Optional[Dict[str, Any]] = None
    group_by: Optional[str] = None      # Field to group rows by
    show_subtotals: bool = False
    subtotal_fields: List[str] = field(default_factory=list)
    max_rows: Optional[int] = None
    empty_message: str = "No items"


@dataclass
class ChartSection:
    """Configuration for a chart section."""
    chart_type: Literal["bar", "line", "pie", "horizontal_bar", "stacked_bar", "donut"]
    title: str
    data_source: str                    # Path to data or "aggregate"
    label_field: str                    # Field for labels/categories
    value_field: str                    # Field for values
    series_field: Optional[str] = None  # For multi-series charts
    colors: Optional[List[str]] = None
    width: float = 6.0
    height: float = 4.0
    show_legend: bool = True
    show_values: bool = True


@dataclass
class ImageSection:
    """Configuration for an image section."""
    source: Literal["field", "static", "logo", "attachment"]
    path: Optional[str] = None          # Field path if source is "field"
    url: Optional[str] = None           # Static URL if source is "static"
    width: Optional[float] = None       # Width in inches
    height: Optional[float] = None      # Height in inches
    alignment: Alignment = Alignment.LEFT
    caption: Optional[str] = None


@dataclass
class TextSection:
    """Configuration for a text/content section."""
    content: str                        # Can include {field_path} placeholders
    style: Optional[Dict[str, Any]] = None  # Font, size, color, etc.


@dataclass
class HeaderSection:
    """Configuration for document header section."""
    fields: List[FieldMapping] = field(default_factory=list)
    layout: Literal["horizontal", "vertical", "grid"] = "horizontal"
    columns: int = 2                    # For grid layout
    show_labels: bool = True
    logo: Optional[ImageSection] = None
    title_template: Optional[str] = None  # e.g., "{Number} - {Description}"


@dataclass
class DetailSection:
    """Configuration for detail/form section."""
    fields: List[FieldMapping] = field(default_factory=list)
    layout: Literal["horizontal", "vertical", "grid"] = "grid"
    columns: int = 2
    show_labels: bool = True
    label_width: Optional[float] = None


@dataclass
class SignatureSection:
    """Configuration for signature blocks."""
    lines: List[Dict[str, str]] = field(default_factory=list)  # [{"label": "Approved By", "path": "ApprovedBy.Name"}]
    show_date_line: bool = True
    columns: int = 2


@dataclass
class Section:
    """A section in the template."""
    type: SectionType
    title: Optional[str] = None
    order: int = 0
    condition: Optional[Dict[str, Any]] = None  # Show section only if condition met
    
    # Type-specific config (only one should be set based on type)
    header_config: Optional[HeaderSection] = None
    detail_config: Optional[DetailSection] = None
    table_config: Optional[TableSection] = None
    chart_config: Optional[ChartSection] = None
    image_config: Optional[ImageSection] = None
    text_config: Optional[TextSection] = None
    signature_config: Optional[SignatureSection] = None
    
    # Styling
    background_color: Optional[str] = None
    border: Optional[Dict[str, Any]] = None
    padding: Optional[Dict[str, float]] = None  # top, right, bottom, left
    margin: Optional[Dict[str, float]] = None


@dataclass
class PageLayout:
    """Page layout configuration."""
    orientation: Orientation = Orientation.PORTRAIT
    margin_top: float = 1.0             # inches
    margin_bottom: float = 1.0
    margin_left: float = 1.0
    margin_right: float = 1.0
    header_height: float = 0.5
    footer_height: float = 0.5


@dataclass
class StyleConfig:
    """Global style configuration."""
    primary_color: str = "#1a365d"
    secondary_color: str = "#3182ce"
    accent_color: str = "#38b2ac"
    
    # Typography
    font_family: str = "Calibri"
    heading_font: str = "Calibri"
    title_size: int = 24
    heading_size: int = 14
    body_size: int = 11
    
    # Table styles
    table_header_bg: str = "#1a365d"
    table_header_fg: str = "#ffffff"
    table_alt_row_bg: str = "#f7fafc"
    table_border_color: str = "#e2e8f0"


@dataclass
class PortableTemplate:
    """
    Complete portable template definition.
    This is the main schema that gets stored and used for report generation.
    """
    name: str
    description: Optional[str] = None
    version: str = "1.0"
    
    # Target entity configuration
    target_entity_def: str = ""         # Primary entity: "kahua_Contract.Contract"
    target_entity_aliases: List[str] = field(default_factory=list)  # Alternative names
    
    # Layout
    layout: PageLayout = field(default_factory=PageLayout)
    style: StyleConfig = field(default_factory=StyleConfig)
    
    # Content sections
    sections: List[Section] = field(default_factory=list)
    
    # Metadata
    id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    created_by: Optional[str] = None
    category: str = "custom"
    tags: List[str] = field(default_factory=list)
    is_public: bool = False
    
    # Source tracking (for templates created from examples)
    source_type: Optional[str] = None   # "upload", "description", "clone"
    source_reference: Optional[str] = None  # Original file name or template ID
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    @staticmethod
    def _convert_field_mapping(f: Dict[str, Any]) -> FieldMapping:
        """Convert a dict to FieldMapping with proper enum handling."""
        if "format" in f and isinstance(f["format"], str):
            f["format"] = FieldFormat(f["format"])
        return FieldMapping(**f)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PortableTemplate":
        """Create from dictionary."""
        # Handle nested dataclasses
        if "layout" in data and isinstance(data["layout"], dict):
            data["layout"] = PageLayout(**data["layout"])
        if "style" in data and isinstance(data["style"], dict):
            data["style"] = StyleConfig(**data["style"])
        
        # Handle sections
        if "sections" in data:
            sections = []
            for s in data["sections"]:
                if isinstance(s, dict):
                    # Convert nested configs
                    section_type = SectionType(s.get("type", "text"))
                    s["type"] = section_type
                    
                    # Convert section config dataclasses
                    if "header_config" in s and isinstance(s["header_config"], dict):
                        hc = s["header_config"]
                        # Convert FieldMapping list
                        if "fields" in hc and isinstance(hc["fields"], list):
                            hc["fields"] = [cls._convert_field_mapping(f) if isinstance(f, dict) else f for f in hc["fields"]]
                        s["header_config"] = HeaderSection(**hc)
                    
                    if "detail_config" in s and isinstance(s["detail_config"], dict):
                        dc = s["detail_config"]
                        if "fields" in dc and isinstance(dc["fields"], list):
                            dc["fields"] = [cls._convert_field_mapping(f) if isinstance(f, dict) else f for f in dc["fields"]]
                        s["detail_config"] = DetailSection(**dc)
                    
                    if "table_config" in s and isinstance(s["table_config"], dict):
                        tc = s["table_config"]
                        if "columns" in tc and isinstance(tc["columns"], list):
                            converted_cols = []
                            for c in tc["columns"]:
                                if isinstance(c, dict):
                                    # Convert nested FieldMapping in column
                                    if "field" in c and isinstance(c["field"], dict):
                                        c["field"] = cls._convert_field_mapping(c["field"])
                                    # Convert Alignment enum
                                    if "alignment" in c and isinstance(c["alignment"], str):
                                        c["alignment"] = Alignment(c["alignment"])
                                    converted_cols.append(ColumnDef(**c))
                                else:
                                    converted_cols.append(c)
                            tc["columns"] = converted_cols
                        s["table_config"] = TableSection(**tc)
                    
                    if "chart_config" in s and isinstance(s["chart_config"], dict):
                        s["chart_config"] = ChartSection(**s["chart_config"])
                    
                    if "image_config" in s and isinstance(s["image_config"], dict):
                        s["image_config"] = ImageSection(**s["image_config"])
                    
                    if "text_config" in s and isinstance(s["text_config"], dict):
                        s["text_config"] = TextSection(**s["text_config"])
                    
                    if "signature_config" in s and isinstance(s["signature_config"], dict):
                        s["signature_config"] = SignatureSection(**s["signature_config"])
                    
                    sections.append(Section(**s))
                else:
                    sections.append(s)
            data["sections"] = sections
        
        # Handle field aliases (template_id -> id, entity_def -> target_entity_def)
        if "template_id" in data and "id" not in data:
            data["id"] = data.pop("template_id")
        elif "template_id" in data:
            del data["template_id"]
        if "entity_def" in data and "target_entity_def" not in data:
            data["target_entity_def"] = data.pop("entity_def")
        elif "entity_def" in data:
            del data["entity_def"]
        
        # Filter to only valid fields
        import dataclasses
        valid_fields = {f.name for f in dataclasses.fields(cls)}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        
        return cls(**filtered_data)
    
    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)
    
    @classmethod
    def from_json(cls, json_str: str) -> "PortableTemplate":
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))


# ============== Factory Functions for Common Template Patterns ==============

def create_simple_report_template(
    name: str,
    entity_def: str,
    header_fields: List[str],
    detail_fields: List[str],
    description: str = ""
) -> PortableTemplate:
    """Create a simple header + details template."""
    
    header_section = Section(
        type=SectionType.HEADER,
        order=0,
        header_config=HeaderSection(
            fields=[FieldMapping(path=f) for f in header_fields],
            layout="grid",
            columns=2
        )
    )
    
    detail_section = Section(
        type=SectionType.DETAIL,
        title="Details",
        order=1,
        detail_config=DetailSection(
            fields=[FieldMapping(path=f) for f in detail_fields],
            layout="grid",
            columns=2
        )
    )
    
    return PortableTemplate(
        name=name,
        description=description,
        target_entity_def=entity_def,
        sections=[header_section, detail_section]
    )


def create_table_report_template(
    name: str,
    entity_def: str,
    header_fields: List[str],
    table_source: str,
    table_columns: List[Dict[str, str]],
    description: str = ""
) -> PortableTemplate:
    """Create a header + table template."""
    
    header_section = Section(
        type=SectionType.HEADER,
        order=0,
        header_config=HeaderSection(
            fields=[FieldMapping(path=f) for f in header_fields],
            layout="horizontal"
        )
    )
    
    columns = [
        ColumnDef(
            field=FieldMapping(path=col["path"], label=col.get("label")),
            alignment=Alignment(col.get("align", "left"))
        )
        for col in table_columns
    ]
    
    table_section = Section(
        type=SectionType.TABLE,
        title="Items",
        order=1,
        table_config=TableSection(
            source=table_source,
            columns=columns
        )
    )
    
    return PortableTemplate(
        name=name,
        description=description,
        target_entity_def=entity_def,
        sections=[header_section, table_section]
    )


# ============== Example Templates ==============

EXAMPLE_CONTRACT_TEMPLATE = PortableTemplate(
    name="Contract Summary",
    description="Standard contract summary with line items table",
    target_entity_def="kahua_Contract.Contract",
    target_entity_aliases=["contract", "contracts"],
    layout=PageLayout(orientation=Orientation.PORTRAIT),
    style=StyleConfig(
        primary_color="#1a365d",
        secondary_color="#3182ce"
    ),
    sections=[
        Section(
            type=SectionType.HEADER,
            order=0,
            header_config=HeaderSection(
                title_template="{Number} - {Description}",
                fields=[
                    FieldMapping(path="Number", label="Contract #"),
                    FieldMapping(path="ContractorCompany.ShortLabel", label="Contractor"),
                    FieldMapping(path="Status.Name", label="Status"),
                    FieldMapping(path="Date", label="Date", format=FieldFormat.DATE),
                ],
                layout="grid",
                columns=2
            )
        ),
        Section(
            type=SectionType.DETAIL,
            title="Contract Details",
            order=1,
            detail_config=DetailSection(
                fields=[
                    FieldMapping(path="Type", label="Type"),
                    FieldMapping(path="ScopeOfWork", label="Scope of Work"),
                    FieldMapping(path="ScheduleStart", label="Start Date", format=FieldFormat.DATE),
                    FieldMapping(path="ScheduleEnd", label="End Date", format=FieldFormat.DATE),
                    FieldMapping(path="OriginalContractAmount", label="Original Amount", format=FieldFormat.CURRENCY),
                    FieldMapping(path="CurrentContractAmount", label="Current Amount", format=FieldFormat.CURRENCY),
                ],
                layout="grid",
                columns=2
            )
        ),
        Section(
            type=SectionType.TABLE,
            title="Contract Items",
            order=2,
            table_config=TableSection(
                source="Items",
                entity_def="kahua_Contract.ContractItem",
                columns=[
                    ColumnDef(field=FieldMapping(path="Number", label="#"), width=0.75),
                    ColumnDef(field=FieldMapping(path="Description", label="Description"), width=3.0),
                    ColumnDef(
                        field=FieldMapping(path="TotalValue", label="Amount", format=FieldFormat.CURRENCY),
                        width=1.5,
                        alignment=Alignment.RIGHT
                    ),
                ],
                show_subtotals=True,
                subtotal_fields=["TotalValue"]
            )
        )
    ],
    category="cost",
    tags=["contract", "cost", "items"]
)


EXAMPLE_DAILY_REPORT_TEMPLATE = PortableTemplate(
    name="Daily Report",
    description="Field daily report with weather, labor, and notes",
    target_entity_def="kahua_AEC_DailyReport.DailyReport",
    target_entity_aliases=["daily report", "daily", "field report"],
    layout=PageLayout(orientation=Orientation.PORTRAIT),
    sections=[
        Section(
            type=SectionType.HEADER,
            order=0,
            header_config=HeaderSection(
                title_template="Daily Report - {Date}",
                fields=[
                    FieldMapping(path="Date", label="Report Date", format=FieldFormat.DATE),
                    FieldMapping(path="Author.ShortLabel", label="Author"),
                    FieldMapping(path="DomainPartition.Name", label="Project"),
                ],
                layout="grid",
                columns=2
            )
        ),
        Section(
            type=SectionType.DETAIL,
            title="Weather Conditions",
            order=1,
            detail_config=DetailSection(
                fields=[
                    FieldMapping(path="Weather", label="Weather"),
                    FieldMapping(path="Temperature", label="Temperature"),
                    FieldMapping(path="Precipitation", label="Precipitation"),
                ],
                layout="horizontal"
            )
        ),
        Section(
            type=SectionType.TABLE,
            title="Labor",
            order=2,
            table_config=TableSection(
                source="LaborEntries",
                columns=[
                    ColumnDef(field=FieldMapping(path="Company.ShortLabel", label="Company")),
                    ColumnDef(field=FieldMapping(path="Trade", label="Trade")),
                    ColumnDef(field=FieldMapping(path="Workers", label="Workers"), alignment=Alignment.RIGHT),
                    ColumnDef(field=FieldMapping(path="Hours", label="Hours"), alignment=Alignment.RIGHT),
                ]
            )
        ),
        Section(
            type=SectionType.TEXT,
            title="Work Performed",
            order=3,
            text_config=TextSection(content="{WorkPerformed}")
        ),
        Section(
            type=SectionType.TEXT,
            title="Notes",
            order=4,
            text_config=TextSection(content="{Notes}")
        )
    ],
    category="field",
    tags=["daily", "field", "labor", "weather"]
)
