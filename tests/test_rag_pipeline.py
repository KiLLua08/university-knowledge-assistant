"""RAG pipeline tests with mocked retrieval and LLM (no LM Studio needed)."""

from types import SimpleNamespace

import pytest

import university_knowledge_assistant.pipelines.rag_pipeline as rag_module
from university_knowledge_assistant.config import Settings
from university_knowledge_assistant.pipelines import (
    NO_CONTEXT_ANSWER,
    SYSTEM_PROMPT,
    RAGPipeline,
    build_context,
    build_sources,
    build_user_prompt,
)


def _result(chunk_id: str, page_number: int = 3) -> dict[str, object]:
    return {
        "id": chunk_id,
        "text": f"Technical text for {chunk_id}.",
        "metadata": {
            "filename": "machine-learning.pdf",
            "page_number": page_number,
            "document_id": "ml-course",
            "chunk_id": chunk_id,
        },
        "distance": 0.15,
    }


class FakeVectorStore:
    def __init__(self, results: list[dict[str, object]]) -> None:
        self.results = results
        self.search_calls: list[tuple[object, int]] = []

    def search(self, query_embedding: object, *, top_k: int) -> list[dict[str, object]]:
        self.search_calls.append((query_embedding, top_k))
        return self.results


class FakeLLMService:
    def __init__(self, answer: str = "Backprop adjusts network weights.") -> None:
        self.answer = answer
        self.calls: list[tuple[str, str]] = []

    def generate_answer(self, system_prompt: str, user_prompt: str) -> str:
        self.calls.append((system_prompt, user_prompt))
        return self.answer


@pytest.fixture
def pipeline_factory(monkeypatch):
    """Build a pipeline with all heavy dependencies replaced by fakes."""
    embed_calls: list[tuple[list[str], object]] = []

    def fake_embed_texts(texts, model):
        embed_calls.append((list(texts), model))
        return [[0.1, 0.2] for _ in texts]

    monkeypatch.setattr(rag_module, "embed_texts", fake_embed_texts)

    def factory(
        results: list[dict[str, object]],
        *,
        retrieval_top_k: int = 2,
        answer: str = "Backprop adjusts network weights.",
    ):
        embedding_model = SimpleNamespace(name="fake-minilm")
        vector_store = FakeVectorStore(results)
        llm_service = FakeLLMService(answer)
        settings = Settings(retrieval_top_k=retrieval_top_k)
        pipeline = RAGPipeline(
            settings=settings,
            embedding_model=embedding_model,
            vector_store=vector_store,
            llm_service=llm_service,
        )
        return pipeline, embedding_model, vector_store, llm_service, embed_calls

    return factory


def test_build_context_labels_file_and_page() -> None:
    context = build_context([_result("chunk-1", page_number=7)])

    assert "[Source 1]" in context
    assert "Filename: machine-learning.pdf" in context
    assert "Page: 7" in context
    assert "Document ID: ml-course" in context
    assert "Text:" in context
    assert "Technical text for chunk-1." in context


def test_build_sources_deduplicates_retrieved_metadata() -> None:
    results = [_result("chunk-1"), _result("chunk-2"), _result("chunk-1")]

    sources = build_sources(results)

    assert sources == [
        {
            "filename": "machine-learning.pdf",
            "page_number": 3,
            "document_id": "ml-course",
            "chunk_id": "chunk-1",
        },
        {
            "filename": "machine-learning.pdf",
            "page_number": 3,
            "document_id": "ml-course",
            "chunk_id": "chunk-2",
        },
    ]


def test_build_user_prompt_includes_question_and_context() -> None:
    prompt = build_user_prompt("What is backprop?", "[Source 1]\nText: ...")

    assert "Question: What is backprop?" in prompt
    assert "Retrieved context:" in prompt
    assert "[Source 1]" in prompt
    assert "using only the context above" in prompt


def test_answer_uses_shared_embedding_model_and_retrieved_metadata(
    pipeline_factory,
) -> None:
    results = [_result("chunk-1"), _result("chunk-2"), _result("chunk-1")]
    pipeline, embedding_model, store, llm, embed_calls = pipeline_factory(results)

    result = pipeline.answer("  What is backprop?  ")

    assert result == {
        "question": "What is backprop?",
        "answer": "Backprop adjusts network weights.",
        "sources": build_sources(results),
    }
    assert embed_calls == [(["What is backprop?"], embedding_model)]
    assert store.search_calls == [([0.1, 0.2], 2)]
    assert len(llm.calls) == 1

    system_prompt, user_prompt = llm.calls[0]
    assert system_prompt == SYSTEM_PROMPT
    assert "Question: What is backprop?" in user_prompt
    assert "Filename: machine-learning.pdf" in user_prompt
    assert "Page: 3" in user_prompt
    assert "Technical text for chunk-1." in user_prompt


def test_answer_honors_explicit_top_k(pipeline_factory) -> None:
    pipeline, _, store, _, _ = pipeline_factory([_result("chunk-1")])

    pipeline.answer("Question?", top_k=5)

    assert store.search_calls == [([0.1, 0.2], 5)]


def test_no_chunks_skips_llm_and_returns_no_context_message(pipeline_factory) -> None:
    pipeline, _, store, llm, _ = pipeline_factory([])

    result = pipeline.answer("Unknown topic")

    assert result["answer"] == NO_CONTEXT_ANSWER
    assert "supporting course material" in result["answer"]
    assert result["sources"] == []
    assert result["question"] == "Unknown topic"
    assert len(store.search_calls) == 1
    assert llm.calls == []


@pytest.mark.parametrize("question", ["", "   ", None, 123])
def test_empty_or_invalid_question_is_rejected(pipeline_factory, question) -> None:
    pipeline, _, store, _, _ = pipeline_factory([_result("chunk-1")])

    with pytest.raises(ValueError, match="question must be a non-empty string"):
        pipeline.answer(question)  # type: ignore[arg-type]

    assert store.search_calls == []


@pytest.mark.parametrize("top_k", [0, -1, 1.5, True, "3"])
def test_invalid_top_k_is_rejected(pipeline_factory, top_k) -> None:
    pipeline, _, store, _, _ = pipeline_factory([_result("chunk-1")])

    with pytest.raises(ValueError, match="top_k must be a positive integer"):
        pipeline.answer("Question?", top_k=top_k)  # type: ignore[arg-type]

    assert store.search_calls == []


def test_llm_service_error_propagates(pipeline_factory) -> None:
    pipeline, _, _, llm, _ = pipeline_factory([_result("chunk-1")])
    llm.generate_answer = lambda *_: (_ for _ in ()).throw(RuntimeError("LM Studio unavailable"))

    with pytest.raises(RuntimeError, match="LM Studio unavailable"):
        pipeline.answer("Question?")


def test_heavy_dependencies_are_created_once(monkeypatch) -> None:
    model = SimpleNamespace(name="fake-minilm")
    created: list[str] = []

    class FakeStore:
        def __init__(self, persist_directory: str) -> None:
            created.append(f"store:{persist_directory}")

    class FakeLLM:
        def __init__(self, settings: Settings) -> None:
            created.append(f"llm:{settings.llm_model}")

    monkeypatch.setattr(rag_module, "load_embedding_model", lambda *args: model)
    monkeypatch.setattr(rag_module, "VectorStore", FakeStore)
    monkeypatch.setattr(rag_module, "LLMService", FakeLLM)

    pipeline = RAGPipeline(settings=Settings(chroma_persist_directory="tmp/chroma"))

    assert pipeline.embedding_model is pipeline.embedding_model
    assert pipeline.vector_store is pipeline.vector_store
    assert pipeline.llm_service is pipeline.llm_service
    assert created == [
        "store:tmp/chroma",
        "llm:qwen3.5-9b",
    ]
