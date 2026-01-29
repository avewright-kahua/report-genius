"""
Template module - Schema definitions and archetype system.
"""

from report_genius.templates.schema import (
    PortableViewTemplate,
    Section,
    SectionType,
    FieldDef,
    FieldFormat,
    HeaderConfig,
    DetailConfig,
    TextConfig,
    TableConfig,
    TableColumn,
    LayoutConfig,
    StyleConfig,
    Condition,
    ConditionOperator,
    Alignment,
)

from report_genius.templates.archetypes import (
    TemplateArchetype,
    InformationDensity,
    VisualTone,
    DesignSystem,
    CreativeComposer,
)

__all__ = [
    # Schema
    "PortableViewTemplate",
    "Section",
    "SectionType",
    "FieldDef",
    "FieldFormat",
    "HeaderConfig",
    "DetailConfig",
    "TextConfig",
    "TableConfig",
    "TableColumn",
    "LayoutConfig",
    "StyleConfig",
    "Condition",
    "ConditionOperator",
    "Alignment",
    # Archetypes
    "TemplateArchetype",
    "InformationDensity",
    "VisualTone",
    "DesignSystem",
    "CreativeComposer",
]
