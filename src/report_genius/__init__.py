"""
Report Genius - Portable View Template System for Kahua

A unified system for creating, managing, and rendering portable views
(templates) for Kahua entities using AI-driven design and DOCX generation.

This is the CANONICAL package for report-genius. Import from here.

Example usage:
    from report_genius import PortableViewTemplate, DocxRenderer
    from report_genius.models import RFIModel
    from report_genius.templates import create_detail_section
"""

__version__ = "0.2.0"

# Core template schema
from report_genius.templates.schema import (
    PortableViewTemplate,
    Section,
    SectionType,
    FieldDef,
    FieldFormat,
    FormatOptions,
    Alignment,
    LayoutType,
    LayoutConfig,
    StyleConfig,
    HeaderConfig,
    DetailConfig,
    TextConfig,
    TableConfig,
    TableColumn,
    Condition,
    ConditionOperator,
    PageHeaderFooterConfig,
)

# Template archetypes
from report_genius.templates.archetypes import (
    TemplateArchetype,
    InformationDensity,
    VisualTone,
    DesignSystem,
)

# Rendering (optional - may fail if template_gen not in path)
try:
    from report_genius.rendering import DocxRenderer
except ImportError:
    DocxRenderer = None

# Configuration
from report_genius.config import (
    TEMPLATES_DIR,
    REPORTS_DIR,
    get_templates_dir,
    get_template_path,
)

__all__ = [
    # Version
    "__version__",
    
    # Core schema
    "PortableViewTemplate",
    "Section",
    "SectionType",
    "FieldDef",
    "FieldFormat",
    "FormatOptions",
    "Alignment",
    "LayoutType",
    "LayoutConfig",
    "StyleConfig",
    "HeaderConfig",
    "DetailConfig",
    "TextConfig",
    "TableConfig",
    "TableColumn",
    "Condition",
    "ConditionOperator",
    "PageHeaderFooterConfig",
    
    # Archetypes
    "TemplateArchetype",
    "InformationDensity",
    "VisualTone",
    "DesignSystem",
    
    # Rendering
    "DocxRenderer",
    
    # Configuration
    "TEMPLATES_DIR",
    "REPORTS_DIR",
    "get_templates_dir",
    "get_template_path",
]
