"""Page-level PDF text extraction using PyMuPDF.

Every extracted page keeps its source metadata so that a retrieved chunk can
later be traced back to an exact file and page number. No OCR is performed:
scanned pages simply produce an empty ``text`` value.
"""

from pathlib import Path
from typing import Any, TypedDict

import pymupdf


class PageRecord(TypedDict):
    """Structured record for one page of a PDF."""

    document_id: str
    filename: str
    page_number: int
    text: str


def extract_pdf(pdf_path: str | Path) -> list[PageRecord]:
    """Extract plain text from a PDF, one record per page.

    Args:
        pdf_path: Path to an existing ``.pdf`` file.

    Returns:
        A list of dictionaries with ``document_id``, ``filename``,
        ``page_number`` (1-based) and ``text``. Empty pages are returned as
        records with an empty string so page numbers stay accurate.

    Raises:
        FileNotFoundError: If the path does not exist.
        ValueError: If the path is not a PDF file.
    """
    path = Path(pdf_path)

    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")
    if not path.is_file():
        raise ValueError(f"Expected a file, got a directory: {path}")
    if path.suffix.lower() != ".pdf":
        raise ValueError(f"The supplied file must be a PDF: {path}")

    pages: list[PageRecord] = []
    with pymupdf.open(path) as document:
        for page_number, page in enumerate(document, start=1):
            text: Any = page.get_text("text").strip()
            pages.append(
                {
                    "document_id": path.stem,
                    "filename": path.name,
                    "page_number": page_number,
                    "text": text if isinstance(text, str) else "",
                }
            )

    return pages
