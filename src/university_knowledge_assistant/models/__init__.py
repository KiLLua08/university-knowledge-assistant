"""Embedding model components."""

from .embedding_model import (
    DEFAULT_DEVICE,
    DEFAULT_MODEL_NAME,
    embed_texts,
    load_embedding_model,
)

__all__ = [
    "DEFAULT_DEVICE",
    "DEFAULT_MODEL_NAME",
    "embed_texts",
    "load_embedding_model",
]
