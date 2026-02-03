"""
Backward Compatibility Shim for pv_template_schema

DEPRECATED: Import from report_genius.templates instead.

This module re-exports the canonical schema from report_genius.templates.schema
to maintain backward compatibility during the migration period.
"""

import warnings

warnings.warn(
    "pv_template_schema is deprecated. Import from report_genius.templates instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export everything from the canonical location
from report_genius.templates.schema import (
    # Enums
    SectionType,
    FieldFormat,
    Alignment,
    LayoutType,
    Orientation,
    ConditionOperator,
    
    # Field definitions
    FormatOptions,
    FieldDef,
    Condition,
    HyperlinkDef,
    
    # Section configs
    HeaderConfig,
    DetailConfig,
    TextConfig,
    TableColumn,
    TableConfig,
    ImageConfig,
    DividerConfig,
    SpacerConfig,
    ListConfig,
    SignatureConfig,
    PageHeaderFooterConfig,
    
    # Section and Template
    Section,
    LayoutConfig,
    StyleConfig,
    PortableViewTemplate,
    
    # Builder helpers
    create_header_section,
    create_detail_section,
    create_text_section,
    create_table_section,
    create_divider_section,
)

# Legacy aliases for backward compatibility with old pv_template_schema names
PortableTemplate = PortableViewTemplate
FieldMapping = FieldDef  # Old name

# Old dataclass-based types are now Pydantic models
# These were the most commonly used from the old schema:
HeaderSection = HeaderConfig
DetailSection = DetailConfig
TableSection = TableConfig
TextSection = TextSection if 'TextSection' in dir() else TextConfig
ColumnDef = TableColumn
PageLayout = LayoutConfig

__all__ = [
    # Canonical names
    "SectionType",
    "FieldFormat",
    "Alignment",
    "LayoutType",
    "Orientation",
    "ConditionOperator",
    "FormatOptions",
    "FieldDef",
    "Condition",
    "HyperlinkDef",
    "HeaderConfig",
    "DetailConfig",
    "TextConfig",
    "TableColumn",
    "TableConfig",
    "ImageConfig",
    "DividerConfig",
    "SpacerConfig",
    "ListConfig",
    "SignatureConfig",
    "PageHeaderFooterConfig",
    "Section",
    "LayoutConfig",
    "StyleConfig",
    "PortableViewTemplate",
    "create_header_section",
    "create_detail_section",
    "create_text_section",
    "create_table_section",
    "create_divider_section",
    
    # Legacy aliases
    "PortableTemplate",
    "FieldMapping",
    "HeaderSection",
    "DetailSection",
    "TableSection",
    "TextSection",
    "ColumnDef",
    "PageLayout",
]
