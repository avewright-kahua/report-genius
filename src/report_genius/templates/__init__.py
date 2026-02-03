"""
Template module - Schema definitions and archetype system.

This is the CANONICAL template module for report-genius.
All template-related imports should come from here.
"""

from report_genius.templates.schema import (
    # Core types
    PortableViewTemplate,
    Section,
    SectionType,
    FieldDef,
    FieldFormat,
    FormatOptions,
    Alignment,
    LayoutType,
    Orientation,
    
    # Section configs
    HeaderConfig,
    DetailConfig,
    TextConfig,
    TableConfig,
    TableColumn,
    ImageConfig,
    DividerConfig,
    SpacerConfig,
    ListConfig,
    SignatureConfig,
    
    # Page layout
    LayoutConfig,
    StyleConfig,
    PageHeaderFooterConfig,
    
    # Conditionals
    Condition,
    ConditionOperator,
    HyperlinkDef,
    
    # Builder helpers
    create_header_section,
    create_detail_section,
    create_text_section,
    create_table_section,
    create_divider_section,
)

from report_genius.templates.archetypes import (
    TemplateArchetype,
    InformationDensity,
    VisualTone,
    DesignSystem,
    DesignGuidelines,
)

# Optional: try to import CreativeComposer if available
# TODO: Move creative_composer to report_genius.core module
try:
    from report_genius.core.creative_composer import CreativeComposer
except ImportError:
    try:
        from template_gen.core.creative_composer import CreativeComposer
    except ImportError:
        CreativeComposer = None

__all__ = [
    # Core types
    "PortableViewTemplate",
    "Section",
    "SectionType",
    "FieldDef",
    "FieldFormat",
    "FormatOptions",
    "Alignment",
    "LayoutType",
    "Orientation",
    
    # Section configs
    "HeaderConfig",
    "DetailConfig",
    "TextConfig",
    "TableConfig",
    "TableColumn",
    "ImageConfig",
    "DividerConfig",
    "SpacerConfig",
    "ListConfig",
    "SignatureConfig",
    
    # Page layout
    "LayoutConfig",
    "StyleConfig",
    "PageHeaderFooterConfig",
    
    # Conditionals
    "Condition",
    "ConditionOperator",
    "HyperlinkDef",
    
    # Builder helpers
    "create_header_section",
    "create_detail_section",
    "create_text_section",
    "create_table_section",
    "create_divider_section",
    
    # Archetypes
    "TemplateArchetype",
    "InformationDensity",
    "VisualTone",
    "DesignSystem",
    "DesignGuidelines",
    "CreativeComposer",
]
