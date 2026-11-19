"""Vector storage and retrieval components."""

from .vector_store import (
    DEFAULT_COLLECTION_NAME,
    DEFAULT_PERSIST_DIRECTORY,
    VectorStore,
)

__all__ = [
    "DEFAULT_COLLECTION_NAME",
    "DEFAULT_PERSIST_DIRECTORY",
    "VectorStore",
]
