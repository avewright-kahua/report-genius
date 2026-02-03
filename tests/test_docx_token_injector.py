from __future__ import annotations

import io
import zipfile
from pathlib import Path

from report_genius.injection import analyze_and_inject


FIXTURES_DIR = Path("tests/fixtures/docx")


def _read_document_xml(docx_bytes: bytes) -> str:
    with zipfile.ZipFile(io.BytesIO(docx_bytes), "r") as zf:
        return zf.read("word/document.xml").decode("utf-8")


def _token_for_label(placeholders: list[dict], label: str) -> str:
    for placeholder in placeholders:
        if placeholder["label"].strip().lower() == label.strip().lower():
            return placeholder["suggested_token"]
    raise AssertionError(f"Label not found in placeholders: {label}")


def test_injects_tokens_in_mixed_fixture() -> None:
    docx_bytes = (FIXTURES_DIR / "placeholders_mixed.docx").read_bytes()
    result = analyze_and_inject(docx_bytes, auto_inject=True)

    assert result["injection"]["success"] is True
    assert result["injection"]["tokens_injected"] >= 5

    placeholders = result["analysis"]["placeholders"]
    document_xml = _read_document_xml(result["modified_document"])

    for label in ["ID", "Status", "Date", "Project Number", "Original Contract Sum"]:
        token = _token_for_label(placeholders, label)
        assert token in document_xml


def test_injects_tokens_in_table_fixture() -> None:
    docx_bytes = (FIXTURES_DIR / "placeholders_table.docx").read_bytes()
    result = analyze_and_inject(docx_bytes, auto_inject=True)

    assert result["injection"]["success"] is True
    assert result["injection"]["tokens_injected"] >= 4

    placeholders = result["analysis"]["placeholders"]
    document_xml = _read_document_xml(result["modified_document"])

    for label in ["Contractor", "Amount", "Start Date", "End Date"]:
        token = _token_for_label(placeholders, label)
        assert token in document_xml
