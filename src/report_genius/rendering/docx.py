"""
DOCX Renderer - Re-exports from template_gen for backward compatibility.

This module provides the DocxRenderer class for generating Word documents
from PortableViewTemplate definitions with Kahua placeholder syntax.
"""

from template_gen.docx_renderer import (
    DocxRenderer,
    build_attribute_placeholder,
    build_currency_placeholder,
    build_date_placeholder,
    build_number_placeholder,
    build_boolean_placeholder,
)

__all__ = [
    "DocxRenderer",
    "build_attribute_placeholder",
    "build_currency_placeholder",
    "build_date_placeholder",
    "build_number_placeholder",
    "build_boolean_placeholder",
]
