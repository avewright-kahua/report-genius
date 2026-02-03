"""
Compatibility shim for Kahua token builders.

Canonical import path: report_genius.templates.kahua_tokens
Legacy implementation lives in template_gen.kahua_tokens.
"""

from __future__ import annotations

from template_gen import kahua_tokens as _legacy


def __getattr__(name: str):
    return getattr(_legacy, name)


def __dir__() -> list[str]:
    return [name for name in dir(_legacy) if not name.startswith("_")]


__all__ = __dir__()
