"""Character-based chunking of one cleaned PDF page at a time.

Each chunk keeps the page metadata it came from. Chunk IDs are deterministic
so re-indexing the same PDF updates existing ChromaDB records instead of
creating duplicates.
"""

from collections.abc import Iterable
from typing import Any, TypedDict

DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 150


class ChunkRecord(TypedDict):
    """Structured record ready for Spark processing and embedding."""

    document_id: str
    filename: str
    page_number: int
    chunk_id: str
    chunk_index: int
    text: str


def _validate_parameters(chunk_size: int, chunk_overlap: int) -> None:
    """Reject configurations that would create invalid or endless loops."""
    if not isinstance(chunk_size, int) or chunk_size <= 0:
        raise ValueError("chunk_size must be a positive integer")
    if not isinstance(chunk_overlap, int) or chunk_overlap < 0:
        raise ValueError("chunk_overlap must be a non-negative integer")
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")


def chunk_text(
    text: str,
    *,
    document_id: str,
    filename: str,
    page_number: int,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[ChunkRecord]:
    """Split one page's text into overlapping character-based chunks.

    Args:
        text: Already cleaned text of a single page.
        document_id: Stable identifier of the source document.
        filename: Original filename.
        page_number: 1-based page number of this text.
        chunk_size: Maximum number of characters per chunk.
        chunk_overlap: Number of characters repeated between adjacent chunks.

    Returns:
        Chunk records. An empty or whitespace-only page produces no chunks.
    """
    _validate_parameters(chunk_size, chunk_overlap)

    if not text or not text.strip():
        return []

    chunks: list[ChunkRecord] = []
    step = chunk_size - chunk_overlap  # Strictly positive after validation.
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))
        piece = text[start:end]

        if piece.strip():
            index = len(chunks)
            chunks.append(
                {
                    "document_id": document_id,
                    "filename": filename,
                    "page_number": page_number,
                    "chunk_id": f"{document_id}_p{page_number}_c{index:04d}",
                    "chunk_index": index,
                    "text": piece,
                }
            )

        if end >= len(text):
            break
        start = end - chunk_overlap

    return chunks


def chunk_pages(
    pages: Iterable[dict[str, Any]],
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[ChunkRecord]:
    """Chunk a collection of page records without merging different pages.

    Args:
        pages: Page records produced by ``extract_pdf`` (possibly cleaned).
        chunk_size: Maximum number of characters per chunk.
        chunk_overlap: Number of characters repeated between adjacent chunks.

    Returns:
        All chunks from all pages, with their original page references kept.
    """
    chunks: list[ChunkRecord] = []
    for page in pages:
        chunks.extend(
            chunk_text(
                page["text"],
                document_id=page["document_id"],
                filename=page["filename"],
                page_number=page["page_number"],
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
        )
    return chunks
