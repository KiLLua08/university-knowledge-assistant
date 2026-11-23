"""Retrieval-Augmented Generation pipeline for student questions.

This component wires together the Day 2 embedding/retrieval code and the new
LM Studio service. Sources are taken from retrieval metadata, not parsed from
the LLM's answer, so citations cannot be invented by the model.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, TypedDict

from ..config import Settings, get_settings
from ..models import embed_texts, load_embedding_model
from ..retrieval import VectorStore
from ..services import LLMService

SYSTEM_PROMPT = """You are a study assistant for university course material.

Rules:
1. Answer ONLY using the retrieved context included in the user message.
2. Never invent facts, filenames, page numbers or citations.
3. If the context does not contain enough information, say clearly:
   "The provided course material does not contain enough information to answer this question."
4. Explain concepts in a student-friendly way, but preserve technical terminology.
5. When useful, refer to evidence labels such as [Source 1] that appear in the context.
6. Do not claim that information comes from a document or page that is not shown in the context.
"""

NO_CONTEXT_ANSWER = (
    "I could not find any supporting course material in the indexed documents " "for this question."
)


class SourceReference(TypedDict):
    """Source metadata returned to the caller, independent of the LLM text."""

    filename: str
    page_number: int
    document_id: str
    chunk_id: str


class RAGResult(TypedDict):
    question: str
    answer: str
    sources: list[SourceReference]


def build_context(results: Sequence[dict[str, Any]]) -> str:
    """Render retrieved chunks into a labelled prompt context."""
    blocks: list[str] = []
    for position, result in enumerate(results, start=1):
        metadata = result.get("metadata") or {}
        blocks.append(
            "\n".join(
                [
                    f"[Source {position}]",
                    f"Filename: {metadata.get('filename', 'unknown')}",
                    f"Page: {metadata.get('page_number', 'unknown')}",
                    f"Document ID: {metadata.get('document_id', 'unknown')}",
                    f"Chunk ID: {metadata.get('chunk_id', 'unknown')}",
                    "Text:",
                    str(result.get("text", "")),
                ]
            )
        )
    return "\n\n".join(blocks)


def build_user_prompt(question: str, context: str) -> str:
    """Combine the original question with the labelled context."""
    return (
        f"Question: {question}\n\n"
        f"Retrieved context:\n{context}\n\n"
        "Now write the answer using only the context above."
    )


def build_sources(results: Sequence[dict[str, Any]]) -> list[SourceReference]:
    """Extract unique source references from retrieved chunk metadata."""
    sources: list[SourceReference] = []
    seen: set[tuple[str, str, str, str]] = set()

    for result in results:
        metadata = result.get("metadata") or {}
        filename = str(metadata.get("filename", ""))
        page_number = metadata.get("page_number", 0)
        document_id = str(metadata.get("document_id", ""))
        chunk_id = str(metadata.get("chunk_id", ""))

        key = (filename, str(page_number), document_id, chunk_id)
        if key in seen:
            continue
        seen.add(key)

        sources.append(
            {
                "filename": filename,
                "page_number": page_number,
                "document_id": document_id,
                "chunk_id": chunk_id,
            }
        )

    return sources


class RAGPipeline:
    """Answer a question from indexed course material using a local LLM."""

    def __init__(
        self,
        *,
        settings: Settings | None = None,
        embedding_model: Any | None = None,
        vector_store: Any | None = None,
        llm_service: Any | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        # Dependencies are injectable for tests; otherwise each is created once
        # and reused for the lifetime of this pipeline.
        self._embedding_model = embedding_model
        self._vector_store = vector_store
        self._llm_service = llm_service

    @property
    def embedding_model(self) -> Any:
        if self._embedding_model is None:
            self._embedding_model = load_embedding_model(
                self.settings.embedding_model, self.settings.embedding_device
            )
        return self._embedding_model

    @property
    def vector_store(self) -> Any:
        if self._vector_store is None:
            self._vector_store = VectorStore(self.settings.chroma_persist_directory)
        return self._vector_store

    @property
    def llm_service(self) -> Any:
        if self._llm_service is None:
            self._llm_service = LLMService(self.settings)
        return self._llm_service

    def answer(self, question: str, *, top_k: int | None = None) -> RAGResult:
        """Retrieve evidence, generate a grounded answer and return sources.

        Args:
            question: The student's natural-language question.
            top_k: Number of chunks to retrieve; defaults to configuration.

        Returns:
            A dictionary with ``question``, ``answer`` and ``sources``.

        Raises:
            ValueError: For an empty question or invalid ``top_k``.
            LLMError: If the language-model call fails.
        """
        if not isinstance(question, str) or not question.strip():
            raise ValueError("question must be a non-empty string")
        question = question.strip()

        effective_top_k = self.settings.retrieval_top_k if top_k is None else top_k
        if (
            not isinstance(effective_top_k, int)
            or isinstance(effective_top_k, bool)
            or effective_top_k <= 0
        ):
            raise ValueError("top_k must be a positive integer")

        # The same embedding model used at indexing time encodes the query.
        query_vector = embed_texts([question], self.embedding_model)[0]
        results = self.vector_store.search(query_vector, top_k=effective_top_k)

        if not results:
            return {
                "question": question,
                "answer": NO_CONTEXT_ANSWER,
                "sources": [],
            }

        context = build_context(results)
        answer = self.llm_service.generate_answer(
            SYSTEM_PROMPT, build_user_prompt(question, context)
        )

        return {
            "question": question,
            "answer": answer,
            "sources": build_sources(results),
        }
