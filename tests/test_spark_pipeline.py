"""Small local Spark pipeline test."""

from university_knowledge_assistant.pipelines import process_chunks


def test_process_chunks_filters_empty_text_and_counts_sources() -> None:
    chunks = [
        {
            "document_id": "doc_a",
            "filename": "doc_a.pdf",
            "page_number": 1,
            "chunk_id": "doc_a_p1_c0000",
            "chunk_index": 0,
            "text": "valid chunk",
        },
        {
            "document_id": "doc_a",
            "filename": "doc_a.pdf",
            "page_number": 1,
            "chunk_id": "doc_a_p1_c0001",
            "chunk_index": 1,
            "text": "   ",
        },
        {
            "document_id": "doc_b",
            "filename": "doc_b.pdf",
            "page_number": 3,
            "chunk_id": "doc_b_p3_c0000",
            "chunk_index": 0,
            "text": "another chunk",
        },
    ]

    result = process_chunks(chunks)

    assert result.chunk_count == 2
    assert result.document_count == 2
    assert result.page_count == 2
    assert [record["chunk_id"] for record in result.records] == [
        "doc_a_p1_c0000",
        "doc_b_p3_c0000",
    ]
    assert all(record["text"].strip() for record in result.records)
