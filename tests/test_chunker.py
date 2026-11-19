"""Tests for character chunking and metadata preservation."""

import pytest

from university_knowledge_assistant.preprocessing import (
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    chunk_pages,
    chunk_text,
)


def _base_metadata() -> dict[str, object]:
    return {
        "document_id": "deep_learning",
        "filename": "deep_learning.pdf",
        "page_number": 4,
    }


def test_chunk_text_preserves_metadata_and_creates_unique_ids() -> None:
    chunks = chunk_text("abcdefghij", **_base_metadata(), chunk_size=6, chunk_overlap=2)

    assert len(chunks) == 2
    assert chunks[0]["text"] == "abcdef"
    assert chunks[1]["text"] == "efghij"
    assert [chunk["chunk_index"] for chunk in chunks] == [0, 1]
    assert len({chunk["chunk_id"] for chunk in chunks}) == 2
    for chunk in chunks:
        assert chunk["document_id"] == "deep_learning"
        assert chunk["filename"] == "deep_learning.pdf"
        assert chunk["page_number"] == 4


def test_chunk_ids_are_deterministic_for_idempotent_indexing() -> None:
    first = chunk_text("some text", **_base_metadata(), chunk_size=5, chunk_overlap=1)
    second = chunk_text("some text", **_base_metadata(), chunk_size=5, chunk_overlap=1)

    assert [chunk["chunk_id"] for chunk in first] == [
        chunk["chunk_id"] for chunk in second
    ]


def test_chunk_pages_does_not_merge_pages() -> None:
    pages = [
        {
            "document_id": "doc",
            "filename": "doc.pdf",
            "page_number": 1,
            "text": "PAGE-ONE",
        },
        {
            "document_id": "doc",
            "filename": "doc.pdf",
            "page_number": 2,
            "text": "PAGE-TWO",
        },
    ]

    chunks = chunk_pages(pages, chunk_size=20, chunk_overlap=0)

    assert [chunk["page_number"] for chunk in chunks] == [1, 2]
    assert [chunk["text"] for chunk in chunks] == ["PAGE-ONE", "PAGE-TWO"]
    assert chunks[0]["chunk_id"] != chunks[1]["chunk_id"]


def test_chunk_text_handles_empty_text() -> None:
    assert chunk_text("", **_base_metadata()) == []
    assert chunk_text("   \n  ", **_base_metadata()) == []


@pytest.mark.parametrize(
    ("chunk_size", "chunk_overlap"),
    [(0, 0), (-1, 0), (10, -1), (10, 10), (10, 11)],
)
def test_chunk_text_rejects_invalid_parameters(
    chunk_size: int, chunk_overlap: int
) -> None:
    with pytest.raises(ValueError):
        chunk_text(
            "abc",
            **_base_metadata(),
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )


def test_default_chunk_parameters() -> None:
    assert DEFAULT_CHUNK_SIZE == 1000
    assert DEFAULT_CHUNK_OVERLAP == 150
