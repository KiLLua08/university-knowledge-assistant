"""Document ingestion components."""

from .pdf_loader import PageRecord, extract_pdf

__all__ = ["PageRecord", "extract_pdf"]
