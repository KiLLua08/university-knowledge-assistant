"""FastAPI dependencies with process-wide component reuse."""

from functools import lru_cache

from ..pipelines import RAGPipeline


@lru_cache(maxsize=1)
def get_rag_pipeline() -> RAGPipeline:
    """Return one RAG pipeline for the whole application lifetime."""
    return RAGPipeline()
