"""
DOCX Renderer - Word document generation from PortableViewTemplate.

This module provides the SOTA (State-of-the-Art) DOCX renderer for generating
professional Word documents from template definitions with Kahua placeholder syntax.

The renderer supports:
- Professional visual hierarchy with proper typography
- Styled tables with alternating rows and proper borders
- Flexible header layouts with logo positioning
- Field groupings with visual separation
- Modern color schemes and spacing
- Page headers/footers with page numbers
"""

# Import the SOTA renderer - this is the canonical implementation
# TODO: After full consolidation, move renderer code into this module
try:
    from template_gen.docx_renderer_sota import (
        SOTADocxRenderer,
        DesignTokens,
        # Placeholder builders
        build_attribute,
        build_currency,
        build_number,
        build_date,
        build_start_table,
        build_end_table,
        build_if,
        format_placeholder,
        # Utilities
        hex_to_rgb,
    )
    # Re-export as canonical names
    DocxRenderer = SOTADocxRenderer
except ImportError:
    # Fallback to basic renderer
    from template_gen.docx_renderer import (
        DocxRenderer,
        build_attribute_placeholder as build_attribute,
        build_currency_placeholder as build_currency,
        build_date_placeholder as build_date,
        build_number_placeholder as build_number,
        build_boolean_placeholder,
    )
    DesignTokens = None
    build_start_table = None
    build_end_table = None
    build_if = None
    format_placeholder = None
    hex_to_rgb = None


__all__ = [
    "DocxRenderer",
    "DesignTokens",
    "build_attribute",
    "build_currency",
    "build_number",
    "build_date",
    "build_start_table",
    "build_end_table",
    "build_if",
    "format_placeholder",
    "hex_to_rgb",
]
