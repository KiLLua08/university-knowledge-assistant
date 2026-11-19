"""Tests for PyMuPDF page extraction."""

from pathlib import Path

import pymupdf
import pytest

from university_knowledge_assistant.data import extract_pdf


def _create_pdf(path: Path, page_texts: list[str]) -> None:
    document = pymupdf.open()
    for text in page_texts:
        page = document.new_page()
        if text:
            page.insert_text((72, 72), text, fontsize=11)
    document.save(path)
    document.close()


def test_extract_pdf_preserves_page_metadata(tmp_path: Path) -> None:
    pdf_path = tmp_path / "course_notes.pdf"
    _create_pdf(pdf_path, ["Deep learning notes", "Second page content"])

    pages = extract_pdf(pdf_path)

    assert len(pages) == 2
    assert pages[0] == {
        "document_id": "course_notes",
        "filename": "course_notes.pdf",
        "page_number": 1,
        "text": "Deep learning notes",
    }
    assert pages[1]["page_number"] == 2
    assert pages[1]["text"] == "Second page content"


def test_extract_pdf_handles_empty_pages(tmp_path: Path) -> None:
    pdf_path = tmp_path / "with_blank_page.pdf"
    _create_pdf(pdf_path, ["Text on first page", ""])

    pages = extract_pdf(pdf_path)

    assert len(pages) == 2
    assert pages[1]["text"] == ""
    assert pages[1]["page_number"] == 2


def test_extract_pdf_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        extract_pdf(tmp_path / "missing.pdf")


def test_extract_pdf_rejects_non_pdf_file(tmp_path: Path) -> None:
    text_file = tmp_path / "notes.txt"
    text_file.write_text("not a pdf", encoding="utf-8")

    with pytest.raises(ValueError, match="must be a PDF"):
        extract_pdf(text_file)
