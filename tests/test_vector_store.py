"""ChromaDB insertion and retrieval tests using a temporary database."""

from pathlib import Path

import numpy as np
import pytest

from university_knowledge_assistant.models import embed_texts
from university_knowledge_assistant.retrieval import VectorStore


class FakeEmbeddingModel:
    """Deterministic keyword-based vectors for fast, offline tests."""

    def encode(self, texts: list[str], **kwargs: object) -> np.ndarray:
        vectors = []
        for text in texts:
            lowered = text.lower()
            if "neural" in lowered:
                vectors.append([1.0, 0.0, 0.0, 0.0])
            elif "spark" in lowered:
                vectors.append([0.0, 1.0, 0.0, 0.0])
            else:
                vectors.append([0.0, 0.0, 1.0, 0.0])
        return np.array(vectors, dtype=np.float32)


def _chunk(chunk_id: str, page: int, text: str) -> dict[str, object]:
    return {
        "document_id": "deep_learning",
        "filename": "deep_learning.pdf",
        "page_number": page,
        "chunk_id": chunk_id,
        "chunk_index": page - 1,
        "text": text,
    }


def test_vector_store_upsert_is_idempotent_and_search_returns_metadata(
    tmp_path: Path,
) -> None:
    store = VectorStore(tmp_path / "chroma")
    model = FakeEmbeddingModel()
    chunks = [
        _chunk("deep_learning_p1_c0000", 1, "A neural network learns weights."),
        _chunk("deep_learning_p2_c0000", 2, "Spark processes large datasets."),
    ]
    embeddings = embed_texts([str(chunk["text"]) for chunk in chunks], model)  # type: ignore[arg-type]

    assert store.search(embeddings[0], top_k=3) == []  # Empty collection is safe.

    assert store.upsert_chunks(chunks, embeddings) == 2  # type: ignore[arg-type]
    assert store.count() == 2

    # Re-indexing the same chunks must not create duplicates.
    store.upsert_chunks(chunks, embeddings)  # type: ignore[arg-type]
    assert store.count() == 2

    results = store.search(embeddings[0], top_k=3)  # type: ignore[arg-type]
    assert len(results) == 2
    assert results[0]["id"] == "deep_learning_p1_c0000"
    assert "neural network" in results[0]["text"]
    assert results[0]["metadata"]["filename"] == "deep_learning.pdf"
    assert results[0]["metadata"]["page_number"] == 1
    assert results[0]["metadata"]["chunk_id"] == "deep_learning_p1_c0000"
    assert results[0]["metadata"]["document_id"] == "deep_learning"
    assert results[0]["distance"] <= results[1]["distance"]


def test_vector_store_respects_top_k_and_validates_arguments(tmp_path: Path) -> None:
    store = VectorStore(tmp_path / "chroma")
    model = FakeEmbeddingModel()
    chunks = [
        _chunk("doc_p1_c0000", 1, "neural network"),
        _chunk("doc_p2_c0000", 2, "spark dataset"),
    ]
    embeddings = embed_texts([str(chunk["text"]) for chunk in chunks], model)  # type: ignore[arg-type]
    store.upsert_chunks(chunks, embeddings)  # type: ignore[arg-type]

    assert len(store.search(embeddings[0], top_k=1)) == 1  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="same length"):
        store.upsert_chunks(chunks, embeddings[:1])  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="top_k"):
        store.search(embeddings[0], top_k=0)  # type: ignore[arg-type]
