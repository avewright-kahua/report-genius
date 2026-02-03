#!/usr/bin/env python3
"""
Lightweight eval harness for agent routing + DOCX injection.

Usage:
  python scripts/eval_agent.py
"""

from __future__ import annotations

import io
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from report_genius.agent.graph import _classify_intent  # noqa: E402
from report_genius.injection import analyze_and_inject  # noqa: E402


FIXTURES_DIR = ROOT / "tests" / "fixtures" / "docx"


def _read_document_xml(docx_bytes: bytes) -> str:
    with zipfile.ZipFile(io.BytesIO(docx_bytes), "r") as zf:
        return zf.read("word/document.xml").decode("utf-8")


def eval_routing() -> list[str]:
    cases = [
        ("inject tokens into this docx", "injection"),
        ("upload template and inject", "injection"),
        ("create a portable view template", "template"),
        ("build a template for rfi", "template"),
        ("show me the latest rfis", "analytics"),
        ("summary report for contracts", "analytics"),
    ]
    failures = []
    for text, expected in cases:
        actual = _classify_intent(text)
        if actual != expected:
            failures.append(f"routing: '{text}' -> {actual} (expected {expected})")
    return failures


def eval_injection() -> list[str]:
    failures = []
    for filename in ["placeholders_mixed.docx", "placeholders_table.docx"]:
        docx_bytes = (FIXTURES_DIR / filename).read_bytes()
        result = analyze_and_inject(docx_bytes, auto_inject=True)
        if not result.get("injection", {}).get("success"):
            failures.append(f"injection: {filename} failed: {result.get('injection')}")
            continue
        if result["injection"]["tokens_injected"] <= 0:
            failures.append(f"injection: {filename} did not inject tokens")
        doc_xml = _read_document_xml(result["modified_document"])
        if "[Attribute(" not in doc_xml:
            failures.append(f"injection: {filename} missing Attribute tokens")
        second = analyze_and_inject(result["modified_document"], auto_inject=True)
        if second["injection"]["tokens_injected"] != 0:
            failures.append(f"injection: {filename} not idempotent on re-run")
    return failures


def main() -> int:
    failures = []
    failures.extend(eval_routing())
    failures.extend(eval_injection())

    if failures:
        print("EVAL FAILURES:")
        for f in failures:
            print(f" - {f}")
        return 1

    print("All evals passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
