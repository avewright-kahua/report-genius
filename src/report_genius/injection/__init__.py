"""
Token injection utilities for DOCX templates.

Canonical entrypoints for analyzing templates and injecting Kahua tokens.
"""

from .docx_token_injector import (
    DetectedPlaceholder,
    InjectionPlan,
    InjectionResult,
    analyze_and_inject,
    analyze_document,
    add_logo_placeholder,
    add_timestamp_token,
    inject_tokens,
    LABEL_NORMALIZATIONS,
)

__all__ = [
    "DetectedPlaceholder",
    "InjectionPlan",
    "InjectionResult",
    "analyze_and_inject",
    "analyze_document",
    "add_logo_placeholder",
    "add_timestamp_token",
    "inject_tokens",
    "LABEL_NORMALIZATIONS",
]
