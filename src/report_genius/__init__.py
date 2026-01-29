"""
Report Genius - Portable View Template System for Kahua

A unified system for creating, managing, and rendering portable views
(templates) for Kahua entities using AI-driven design and DOCX generation.
"""

__version__ = "0.1.0"

from report_genius.templates.schema import (
    PortableViewTemplate,
    Section,
    SectionType,
    FieldDef,
    FieldFormat,
    Alignment,
)

from report_genius.templates.archetypes import (
    TemplateArchetype,
    InformationDensity,
    VisualTone,
)

__all__ = [
    # Schema
    "PortableViewTemplate",
    "Section",
    "SectionType",
    "FieldDef",
    "FieldFormat",
    "Alignment",
    # Archetypes
    "TemplateArchetype",
    "InformationDensity",
    "VisualTone",
]
