"""
Word Template Definitions
Serializable template definitions for reusable Word document generation.
Templates store structure and styling; rendering combines them with data.
"""

import json
import uuid
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum

log = logging.getLogger("word_template_defs")

# Storage
TEMPLATES_DIR = Path(__file__).parent / "word_templates"
TEMPLATES_DIR.mkdir(exist_ok=True)


# ============== Section Types ==============

class SectionKind(str, Enum):
    """Types of sections in a Word template."""
    TITLE = "title"              # Document title banner
    HEADER = "header"            # Section header/heading
    FIELD_GRID = "field_grid"    # Label-value pairs in grid
    DATA_TABLE = "data_table"    # Tabular data
    TEXT = "text"                # Paragraph text (supports {placeholders})
    IMAGE = "image"              # Image/logo
    DIVIDER = "divider"          # Horizontal line
    SPACER = "spacer"            # Vertical space
    PAGE_BREAK = "page_break"    # Force new page
    SIGNATURE = "signature"      # Signature block


class FieldFormat(str, Enum):
    TEXT = "text"
    NUMBER = "number"
    CURRENCY = "currency"
    DATE = "date"
    DATETIME = "datetime"
    PERCENT = "percent"
    BOOLEAN = "boolean"


class Alignment(str, Enum):
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


class Orientation(str, Enum):
    PORTRAIT = "portrait"
    LANDSCAPE = "landscape"


# ============== Section Definitions ==============

@dataclass
class FieldDef:
    """Field definition for data binding."""
    path: str                           # Data path: "Status.Name"
    label: Optional[str] = None         # Display label
    format: FieldFormat = FieldFormat.TEXT
    format_options: Optional[Dict[str, Any]] = None
    default: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "path": self.path,
            "label": self.label,
            "format": self.format.value if isinstance(self.format, FieldFormat) else self.format,
            "format_options": self.format_options,
            "default": self.default,
        }
    
    @classmethod
    def from_dict(cls, d: Dict) -> 'FieldDef':
        if "format" in d and isinstance(d["format"], str):
            d["format"] = FieldFormat(d["format"])
        return cls(**d)


@dataclass
class ColumnDef:
    """Column definition for tables."""
    key: str                            # Data path key
    label: str                          # Header label
    format: FieldFormat = FieldFormat.TEXT
    format_options: Optional[Dict[str, Any]] = None
    width: Optional[float] = None       # Width in inches
    align: Alignment = Alignment.LEFT
    
    def to_dict(self) -> Dict:
        return {
            "key": self.key,
            "label": self.label,
            "format": self.format.value if isinstance(self.format, FieldFormat) else self.format,
            "format_options": self.format_options,
            "width": self.width,
            "align": self.align.value if isinstance(self.align, Alignment) else self.align,
        }
    
    @classmethod
    def from_dict(cls, d: Dict) -> 'ColumnDef':
        if "format" in d and isinstance(d["format"], str):
            d["format"] = FieldFormat(d["format"])
        if "align" in d and isinstance(d["align"], str):
            d["align"] = Alignment(d["align"])
        return cls(**d)


@dataclass
class Condition:
    """Conditional display logic."""
    field: str                          # Data path to check
    op: str = "exists"                  # "exists", "eq", "ne", "gt", "lt", "contains", "not_empty"
    value: Any = None                   # Comparison value
    
    def to_dict(self) -> Dict:
        return {"field": self.field, "op": self.op, "value": self.value}
    
    @classmethod
    def from_dict(cls, d: Dict) -> 'Condition':
        return cls(**d)


@dataclass
class TitleSection:
    """Title banner section."""
    text: str                           # Title text (supports {placeholders})
    subtitle: Optional[str] = None      # Subtitle text
    
    def to_dict(self) -> Dict:
        return {"text": self.text, "subtitle": self.subtitle}
    
    @classmethod
    def from_dict(cls, d: Dict) -> 'TitleSection':
        return cls(**d)


@dataclass
class HeaderSection:
    """Section heading."""
    text: str
    level: int = 2                      # Heading level (1-3)
    
    def to_dict(self) -> Dict:
        return {"text": self.text, "level": self.level}
    
    @classmethod
    def from_dict(cls, d: Dict) -> 'HeaderSection':
        return cls(**d)


@dataclass
class FieldGridSection:
    """Grid of label-value pairs."""
    fields: List[FieldDef]
    columns: int = 2
    show_labels: bool = True
    striped: bool = True
    
    def to_dict(self) -> Dict:
        return {
            "fields": [f.to_dict() for f in self.fields],
            "columns": self.columns,
            "show_labels": self.show_labels,
            "striped": self.striped,
        }
    
    @classmethod
    def from_dict(cls, d: Dict) -> 'FieldGridSection':
        if "fields" in d:
            d["fields"] = [FieldDef.from_dict(f) if isinstance(f, dict) else f for f in d["fields"]]
        return cls(**d)


@dataclass
class DataTableSection:
    """Data table section."""
    source: str                         # Data path to array: "Items", "ChangeOrders"
    columns: List[ColumnDef]
    show_header: bool = True
    show_row_numbers: bool = False
    striped: bool = True
    sort_by: Optional[str] = None
    sort_desc: bool = False
    max_rows: Optional[int] = None
    totals: Optional[List[str]] = None  # Column keys to sum
    empty_message: str = "No items"
    
    def to_dict(self) -> Dict:
        return {
            "source": self.source,
            "columns": [c.to_dict() for c in self.columns],
            "show_header": self.show_header,
            "show_row_numbers": self.show_row_numbers,
            "striped": self.striped,
            "sort_by": self.sort_by,
            "sort_desc": self.sort_desc,
            "max_rows": self.max_rows,
            "totals": self.totals,
            "empty_message": self.empty_message,
        }
    
    @classmethod
    def from_dict(cls, d: Dict) -> 'DataTableSection':
        if "columns" in d:
            d["columns"] = [ColumnDef.from_dict(c) if isinstance(c, dict) else c for c in d["columns"]]
        return cls(**d)


@dataclass
class TextSection:
    """Text paragraph section."""
    content: str                        # Text with {placeholders}
    
    def to_dict(self) -> Dict:
        return {"content": self.content}
    
    @classmethod
    def from_dict(cls, d: Dict) -> 'TextSection':
        return cls(**d)


@dataclass
class ImageSection:
    """Image section."""
    source: str                         # "field", "static", "logo"
    path: Optional[str] = None          # Field path or URL
    width: Optional[float] = None       # Inches
    height: Optional[float] = None
    align: Alignment = Alignment.LEFT
    caption: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "source": self.source,
            "path": self.path,
            "width": self.width,
            "height": self.height,
            "align": self.align.value if isinstance(self.align, Alignment) else self.align,
            "caption": self.caption,
        }
    
    @classmethod
    def from_dict(cls, d: Dict) -> 'ImageSection':
        if "align" in d and isinstance(d["align"], str):
            d["align"] = Alignment(d["align"])
        return cls(**d)


@dataclass
class SignatureSection:
    """Signature block."""
    lines: List[Dict[str, str]]         # [{"label": "Approved By", "path": "ApprovedBy.Name"}]
    columns: int = 2
    show_date: bool = True
    
    def to_dict(self) -> Dict:
        return {"lines": self.lines, "columns": self.columns, "show_date": self.show_date}
    
    @classmethod
    def from_dict(cls, d: Dict) -> 'SignatureSection':
        return cls(**d)


@dataclass
class SpacerSection:
    """Vertical spacer."""
    height: float = 12  # Points
    
    def to_dict(self) -> Dict:
        return {"height": self.height}
    
    @classmethod
    def from_dict(cls, d: Dict) -> 'SpacerSection':
        return cls(**d)


@dataclass
class Section:
    """A section in the template."""
    kind: SectionKind
    order: int = 0
    condition: Optional[Condition] = None
    
    # Type-specific config (only one should be set)
    title_config: Optional[TitleSection] = None
    header_config: Optional[HeaderSection] = None
    field_grid_config: Optional[FieldGridSection] = None
    data_table_config: Optional[DataTableSection] = None
    text_config: Optional[TextSection] = None
    image_config: Optional[ImageSection] = None
    signature_config: Optional[SignatureSection] = None
    spacer_config: Optional[SpacerSection] = None
    
    def to_dict(self) -> Dict:
        d = {
            "kind": self.kind.value if isinstance(self.kind, SectionKind) else self.kind,
            "order": self.order,
        }
        if self.condition:
            d["condition"] = self.condition.to_dict()
        
        # Add type-specific config
        config_map = {
            "title_config": self.title_config,
            "header_config": self.header_config,
            "field_grid_config": self.field_grid_config,
            "data_table_config": self.data_table_config,
            "text_config": self.text_config,
            "image_config": self.image_config,
            "signature_config": self.signature_config,
            "spacer_config": self.spacer_config,
        }
        for key, val in config_map.items():
            if val:
                d[key] = val.to_dict() if hasattr(val, 'to_dict') else val
        
        return d
    
    @classmethod
    def from_dict(cls, d: Dict) -> 'Section':
        if "kind" in d and isinstance(d["kind"], str):
            d["kind"] = SectionKind(d["kind"])
        if "condition" in d and isinstance(d["condition"], dict):
            d["condition"] = Condition.from_dict(d["condition"])
        
        # Convert configs
        config_classes = {
            "title_config": TitleSection,
            "header_config": HeaderSection,
            "field_grid_config": FieldGridSection,
            "data_table_config": DataTableSection,
            "text_config": TextSection,
            "image_config": ImageSection,
            "signature_config": SignatureSection,
            "spacer_config": SpacerSection,
        }
        for key, config_cls in config_classes.items():
            if key in d and isinstance(d[key], dict):
                d[key] = config_cls.from_dict(d[key])
        
        return cls(**d)


# ============== Theme Definition ==============

@dataclass
class ThemeDef:
    """Document theme/styling."""
    name: str = "Default"
    
    # Colors
    primary_color: str = "#1a365d"
    secondary_color: str = "#3182ce"
    accent_color: str = "#38b2ac"
    text_color: str = "#1a202c"
    muted_color: str = "#718096"
    
    # Typography
    heading_font: str = "Calibri Light"
    body_font: str = "Calibri"
    title_size: float = 24
    heading1_size: float = 18
    heading2_size: float = 14
    heading3_size: float = 12
    body_size: float = 11
    small_size: float = 9
    
    # Tables
    table_header_bg: str = "#1a365d"
    table_header_fg: str = "#ffffff"
    table_stripe_bg: str = "#f7fafc"
    table_border_color: str = "#e2e8f0"
    
    # Page
    orientation: Orientation = Orientation.PORTRAIT
    margin_top: float = 1.0
    margin_bottom: float = 1.0
    margin_left: float = 1.0
    margin_right: float = 1.0
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "primary_color": self.primary_color,
            "secondary_color": self.secondary_color,
            "accent_color": self.accent_color,
            "text_color": self.text_color,
            "muted_color": self.muted_color,
            "heading_font": self.heading_font,
            "body_font": self.body_font,
            "title_size": self.title_size,
            "heading1_size": self.heading1_size,
            "heading2_size": self.heading2_size,
            "heading3_size": self.heading3_size,
            "body_size": self.body_size,
            "small_size": self.small_size,
            "table_header_bg": self.table_header_bg,
            "table_header_fg": self.table_header_fg,
            "table_stripe_bg": self.table_stripe_bg,
            "table_border_color": self.table_border_color,
            "orientation": self.orientation.value if isinstance(self.orientation, Orientation) else self.orientation,
            "margin_top": self.margin_top,
            "margin_bottom": self.margin_bottom,
            "margin_left": self.margin_left,
            "margin_right": self.margin_right,
        }
    
    @classmethod
    def from_dict(cls, d: Dict) -> 'ThemeDef':
        if "orientation" in d and isinstance(d["orientation"], str):
            d["orientation"] = Orientation(d["orientation"])
        return cls(**d)


# ============== Template Definition ==============

@dataclass
class WordTemplateDef:
    """
    Complete Word template definition.
    Serializable, storable, and reusable.
    """
    name: str
    description: str = ""
    version: str = "1.0"
    
    # Target entity
    entity_def: str = ""                # e.g., "kahua_Contract.Contract"
    entity_aliases: List[str] = field(default_factory=list)
    
    # Content
    sections: List[Section] = field(default_factory=list)
    theme: ThemeDef = field(default_factory=ThemeDef)
    
    # Header/Footer
    header_text: Optional[str] = None
    footer_text: Optional[str] = None
    show_page_numbers: bool = True
    
    # Metadata
    id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    created_by: Optional[str] = None
    category: str = "custom"
    tags: List[str] = field(default_factory=list)
    is_public: bool = False
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "entity_def": self.entity_def,
            "entity_aliases": self.entity_aliases,
            "sections": [s.to_dict() for s in self.sections],
            "theme": self.theme.to_dict() if self.theme else None,
            "header_text": self.header_text,
            "footer_text": self.footer_text,
            "show_page_numbers": self.show_page_numbers,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "created_by": self.created_by,
            "category": self.category,
            "tags": self.tags,
            "is_public": self.is_public,
        }
    
    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)
    
    @classmethod
    def from_dict(cls, d: Dict) -> 'WordTemplateDef':
        if "sections" in d:
            d["sections"] = [Section.from_dict(s) if isinstance(s, dict) else s for s in d["sections"]]
        if "theme" in d and isinstance(d["theme"], dict):
            d["theme"] = ThemeDef.from_dict(d["theme"])
        return cls(**d)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'WordTemplateDef':
        return cls.from_dict(json.loads(json_str))


# ============== Template Registry ==============

class TemplateRegistry:
    """Manages saving, loading, and listing Word templates."""
    
    def __init__(self, storage_dir: Path = None):
        self.storage_dir = storage_dir or TEMPLATES_DIR
        self.storage_dir.mkdir(parents=True, exist_ok=True)
    
    def save(self, template: WordTemplateDef) -> str:
        """Save template and return ID."""
        if not template.id:
            template.id = f"wt-{uuid.uuid4().hex[:8]}"
        
        now = datetime.utcnow().isoformat()
        template.created_at = template.created_at or now
        template.updated_at = now
        
        path = self.storage_dir / f"{template.id}.json"
        with open(path, 'w', encoding='utf-8') as f:
            f.write(template.to_json())
        
        log.info(f"Saved template: {template.id}")
        return template.id
    
    def load(self, template_id: str) -> Optional[WordTemplateDef]:
        """Load template by ID."""
        path = self.storage_dir / f"{template_id}.json"
        if not path.exists():
            log.warning(f"Template not found: {template_id}")
            return None
        
        with open(path, 'r', encoding='utf-8') as f:
            return WordTemplateDef.from_json(f.read())
    
    def delete(self, template_id: str) -> bool:
        """Delete template by ID."""
        path = self.storage_dir / f"{template_id}.json"
        if path.exists():
            path.unlink()
            log.info(f"Deleted template: {template_id}")
            return True
        return False
    
    def list_all(
        self,
        category: str = None,
        entity_def: str = None,
        search: str = None
    ) -> List[Dict[str, Any]]:
        """List all templates with optional filtering."""
        templates = []
        
        for path in self.storage_dir.glob("*.json"):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Apply filters
                    if category and data.get("category") != category:
                        continue
                    if entity_def and data.get("entity_def") != entity_def:
                        continue
                    if search:
                        search_lower = search.lower()
                        name_match = search_lower in data.get("name", "").lower()
                        desc_match = search_lower in data.get("description", "").lower()
                        if not (name_match or desc_match):
                            continue
                    
                    templates.append({
                        "id": data.get("id", path.stem),
                        "name": data.get("name", "Untitled"),
                        "description": data.get("description", "")[:100],
                        "entity_def": data.get("entity_def", ""),
                        "category": data.get("category", "custom"),
                        "created_at": data.get("created_at"),
                        "updated_at": data.get("updated_at"),
                    })
            except Exception as e:
                log.error(f"Error loading template {path}: {e}")
        
        # Sort by updated_at descending
        templates.sort(key=lambda x: x.get("updated_at") or "", reverse=True)
        return templates
    
    def duplicate(self, template_id: str, new_name: str = None) -> Optional[str]:
        """Duplicate a template with a new ID."""
        template = self.load(template_id)
        if not template:
            return None
        
        template.id = None  # Will generate new ID
        template.name = new_name or f"{template.name} (Copy)"
        template.created_at = None
        template.updated_at = None
        
        return self.save(template)


# ============== Factory Functions ==============

def create_field(path: str, label: str = None, format: FieldFormat = FieldFormat.TEXT, **kwargs) -> FieldDef:
    """Helper to create field definitions."""
    return FieldDef(path=path, label=label, format=format, **kwargs)


def create_column(key: str, label: str, format: FieldFormat = FieldFormat.TEXT, align: Alignment = Alignment.LEFT, **kwargs) -> ColumnDef:
    """Helper to create column definitions."""
    return ColumnDef(key=key, label=label, format=format, align=align, **kwargs)


def create_title_section(text: str, subtitle: str = None, order: int = 0) -> Section:
    """Create a title section."""
    return Section(
        kind=SectionKind.TITLE,
        order=order,
        title_config=TitleSection(text=text, subtitle=subtitle)
    )


def create_header_section(text: str, level: int = 2, order: int = 0, condition: Condition = None) -> Section:
    """Create a header/heading section."""
    return Section(
        kind=SectionKind.HEADER,
        order=order,
        condition=condition,
        header_config=HeaderSection(text=text, level=level)
    )


def create_field_grid_section(fields: List[FieldDef], columns: int = 2, order: int = 0, **kwargs) -> Section:
    """Create a field grid section."""
    return Section(
        kind=SectionKind.FIELD_GRID,
        order=order,
        field_grid_config=FieldGridSection(fields=fields, columns=columns, **kwargs)
    )


def create_table_section(
    source: str,
    columns: List[ColumnDef],
    order: int = 0,
    condition: Condition = None,
    **kwargs
) -> Section:
    """Create a data table section."""
    return Section(
        kind=SectionKind.DATA_TABLE,
        order=order,
        condition=condition,
        data_table_config=DataTableSection(source=source, columns=columns, **kwargs)
    )


def create_text_section(content: str, order: int = 0, condition: Condition = None) -> Section:
    """Create a text section."""
    return Section(
        kind=SectionKind.TEXT,
        order=order,
        condition=condition,
        text_config=TextSection(content=content)
    )


# ============== Built-in Templates ==============

def get_contract_template() -> WordTemplateDef:
    """Built-in contract summary template."""
    return WordTemplateDef(
        id="builtin-contract",
        name="Contract Summary",
        description="Professional contract portable view with financials and change orders",
        entity_def="kahua_Contract.Contract",
        category="cost",
        tags=["contract", "cost", "financial"],
        sections=[
            create_title_section("{Number} - {Description}", order=0),
            
            create_field_grid_section([
                create_field("ContractorCompany.ShortLabel", "Contractor"),
                create_field("WorkflowStatus", "Status"),
                create_field("Type", "Type"),
                create_field("CurrencyCode", "Currency"),
            ], columns=2, order=1),
            
            create_header_section("Financials", order=2),
            create_field_grid_section([
                create_field("OriginalContractValue", "Original Value", FieldFormat.CURRENCY),
                create_field("ContractApprovedTotalValue", "Approved Total", FieldFormat.CURRENCY),
                create_field("ContractPendingTotalValue", "Pending", FieldFormat.CURRENCY),
                create_field("BalanceToFinishAmount", "Balance to Finish", FieldFormat.CURRENCY),
            ], columns=2, order=3),
            
            create_header_section("Scope of Work", order=4, condition=Condition("ScopeOfWork", "not_empty")),
            create_text_section("{ScopeOfWork}", order=5, condition=Condition("ScopeOfWork", "not_empty")),
            
            create_header_section("Change Orders", order=6, condition=Condition("ChangeOrders", "not_empty")),
            create_table_section(
                source="ChangeOrders",
                columns=[
                    create_column("Number", "Number"),
                    create_column("Description", "Description"),
                    create_column("ApprovedAmount", "Amount", FieldFormat.CURRENCY, Alignment.RIGHT),
                    create_column("Status", "Status"),
                ],
                order=7,
                condition=Condition("ChangeOrders", "not_empty"),
                totals=["ApprovedAmount"]
            ),
        ],
        theme=ThemeDef(
            primary_color="#0f172a",
            secondary_color="#0369a1",
            accent_color="#059669",
            body_size=10,
            margin_top=0.6,
            margin_bottom=0.6,
            margin_left=0.75,
            margin_right=0.75,
        )
    )


def get_rfi_template() -> WordTemplateDef:
    """Built-in RFI template."""
    return WordTemplateDef(
        id="builtin-rfi",
        name="RFI Summary",
        description="Request for Information portable view",
        entity_def="kahua_AEC_RFI.RFI",
        category="field",
        tags=["rfi", "field", "communication"],
        sections=[
            create_title_section("RFI {Number}", subtitle="{Subject}", order=0),
            
            create_field_grid_section([
                create_field("Status", "Status"),
                create_field("Priority", "Priority"),
                create_field("DateSubmitted", "Submitted", FieldFormat.DATE),
                create_field("DateRequired", "Required By", FieldFormat.DATE),
            ], columns=2, order=1),
            
            create_header_section("Question", order=2),
            create_text_section("{Question}", order=3),
            
            create_header_section("Response", order=4, condition=Condition("Response", "not_empty")),
            create_text_section("{Response}", order=5, condition=Condition("Response", "not_empty")),
            
            create_field_grid_section([
                create_field("SubmittedBy.Name", "Submitted By"),
                create_field("AssignedTo.Name", "Assigned To"),
                create_field("RespondedBy.Name", "Responded By"),
                create_field("DateResponded", "Response Date", FieldFormat.DATE),
            ], columns=2, order=6),
        ],
        theme=ThemeDef(
            primary_color="#1e3a5f",
            secondary_color="#2563eb",
        )
    )


# Singleton registry
_registry: Optional[TemplateRegistry] = None

def get_registry() -> TemplateRegistry:
    """Get the global template registry."""
    global _registry
    if _registry is None:
        _registry = TemplateRegistry()
    return _registry
