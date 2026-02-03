"""
Rendering module - DOCX generation from templates.

Provides professional-grade Word document generation with:
- Kahua placeholder syntax for data binding
- Modern typography and styling
- Table formatting with alternating rows
- Page headers/footers with page numbers

Supports both:
- New Pydantic-based PortableViewTemplate (via DocxRenderer)
- Legacy dataclass-based PortableTemplate (via LegacyRenderer)
"""

from report_genius.rendering.docx import (
    DocxRenderer,
    DesignTokens,
    build_attribute,
    build_currency,
    build_number,
    build_date,
    format_placeholder,
)

# Legacy renderer for old dataclass-based templates
try:
    from pv_template_renderer import TemplateRenderer as LegacyRenderer
except ImportError:
    LegacyRenderer = None

__all__ = [
    "DocxRenderer",
    "LegacyRenderer",
    "DesignTokens",
    "build_attribute",
    "build_currency",
    "build_number",
    "build_date",
    "format_placeholder",
]
