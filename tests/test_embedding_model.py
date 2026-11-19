"""Embedding tests with a fake model so no download is required."""

import numpy as np

import university_knowledge_assistant.models.embedding_model as embedding_model


class FakeSentenceTransformer:
    """Minimal stand-in that records how it was called."""

    def __init__(self, model_name: str, device: str) -> None:
        self.model_name = model_name
        self.device = device
        self.encode_calls = 0

    def encode(self, texts: list[str], **kwargs: object) -> np.ndarray:
        self.encode_calls += 1
        return np.ones((len(texts), 3), dtype=np.float32)


def test_load_embedding_model_uses_requested_model_and_device(monkeypatch) -> None:
    monkeypatch.setattr(embedding_model, "SentenceTransformer", FakeSentenceTransformer)

    model = embedding_model.load_embedding_model("test-model", "cpu")

    assert isinstance(model, FakeSentenceTransformer)
    assert model.model_name == "test-model"
    assert model.device == "cpu"


def test_embed_texts_returns_numeric_vectors_in_order(monkeypatch) -> None:
    monkeypatch.setattr(embedding_model, "SentenceTransformer", FakeSentenceTransformer)
    model = embedding_model.load_embedding_model()

    vectors = embedding_model.embed_texts(["first", "second"], model)

    assert isinstance(vectors, list)
    assert len(vectors) == 2
    assert all(isinstance(vector, list) for vector in vectors)
    assert all(isinstance(value, float) for vector in vectors for value in vector)
    assert all(len(vector) == 3 for vector in vectors)
    assert model.encode_calls == 1  # One batched call, not one per text.


def test_embed_texts_handles_empty_input_without_calling_model(monkeypatch) -> None:
    monkeypatch.setattr(embedding_model, "SentenceTransformer", FakeSentenceTransformer)
    model = embedding_model.load_embedding_model()

    assert embedding_model.embed_texts([], model) == []
    assert model.encode_calls == 0


def test_embed_texts_rejects_non_string_values(monkeypatch) -> None:
    monkeypatch.setattr(embedding_model, "SentenceTransformer", FakeSentenceTransformer)
    model = embedding_model.load_embedding_model()

    try:
        embedding_model.embed_texts([123], model)  # type: ignore[list-item]
    except TypeError:
        pass
    else:
        raise AssertionError("expected a TypeError for non-string input")
