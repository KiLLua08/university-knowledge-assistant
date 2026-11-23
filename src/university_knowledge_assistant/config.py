"""Centralized, environment-variable-based configuration.

All runtime settings live here so the rest of the code does not scatter
hardcoded URLs, model names or thresholds. ``get_settings()`` is cached: the
environment is read once per process, not on every API request.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

DEFAULT_LLM_BASE_URL = "http://localhost:1234/v1"
DEFAULT_LLM_MODEL = "qwen3.5-9b"
DEFAULT_LLM_API_KEY = "lm-studio"
DEFAULT_LLM_TEMPERATURE = 0.2
DEFAULT_LLM_MAX_TOKENS = 2048
DEFAULT_LLM_TIMEOUT_SECONDS = 120.0
DEFAULT_RETRIEVAL_TOP_K = 3
DEFAULT_CHROMA_PERSIST_DIRECTORY = "data/chroma"
DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_EMBEDDING_DEVICE = "cpu"


def _read_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        return float(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number, got {raw!r}") from exc


def _read_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, got {raw!r}") from exc


def _read_text(name: str, default: str) -> str:
    return os.getenv(name, default).strip() or default


@dataclass(frozen=True)
class Settings:
    """Validated application settings."""

    llm_base_url: str = DEFAULT_LLM_BASE_URL
    llm_model: str = DEFAULT_LLM_MODEL
    llm_api_key: str = DEFAULT_LLM_API_KEY
    llm_temperature: float = DEFAULT_LLM_TEMPERATURE
    llm_max_tokens: int = DEFAULT_LLM_MAX_TOKENS
    llm_timeout_seconds: float = DEFAULT_LLM_TIMEOUT_SECONDS
    retrieval_top_k: int = DEFAULT_RETRIEVAL_TOP_K
    chroma_persist_directory: str = DEFAULT_CHROMA_PERSIST_DIRECTORY
    embedding_model: str = DEFAULT_EMBEDDING_MODEL
    embedding_device: str = DEFAULT_EMBEDDING_DEVICE

    def __post_init__(self) -> None:
        if not self.llm_base_url.startswith(("http://", "https://")):
            raise ValueError("LLM_BASE_URL must start with http:// or https://")
        if not self.llm_model:
            raise ValueError("LLM_MODEL must not be empty")
        if not self.llm_api_key:
            raise ValueError("LLM_API_KEY must not be empty")
        if not 0.0 <= self.llm_temperature <= 2.0:
            raise ValueError("LLM_TEMPERATURE must be between 0 and 2")
        if self.llm_max_tokens <= 0:
            raise ValueError("LLM_MAX_TOKENS must be a positive integer")
        if self.llm_timeout_seconds <= 0:
            raise ValueError("LLM_TIMEOUT_SECONDS must be positive")
        if self.retrieval_top_k <= 0:
            raise ValueError("RETRIEVAL_TOP_K must be a positive integer")
        if not self.chroma_persist_directory:
            raise ValueError("CHROMA_PERSIST_DIRECTORY must not be empty")
        if not self.embedding_model:
            raise ValueError("EMBEDDING_MODEL must not be empty")
        if not self.embedding_device:
            raise ValueError("EMBEDDING_DEVICE must not be empty")

    @classmethod
    def from_env(cls) -> Settings:
        """Build settings from environment variables (and a local ``.env``)."""
        load_dotenv()
        return cls(
            llm_base_url=_read_text("LLM_BASE_URL", DEFAULT_LLM_BASE_URL),
            llm_model=_read_text("LLM_MODEL", DEFAULT_LLM_MODEL),
            llm_api_key=_read_text("LLM_API_KEY", DEFAULT_LLM_API_KEY),
            llm_temperature=_read_float("LLM_TEMPERATURE", DEFAULT_LLM_TEMPERATURE),
            llm_max_tokens=_read_int("LLM_MAX_TOKENS", DEFAULT_LLM_MAX_TOKENS),
            llm_timeout_seconds=_read_float("LLM_TIMEOUT_SECONDS", DEFAULT_LLM_TIMEOUT_SECONDS),
            retrieval_top_k=_read_int("RETRIEVAL_TOP_K", DEFAULT_RETRIEVAL_TOP_K),
            chroma_persist_directory=_read_text(
                "CHROMA_PERSIST_DIRECTORY", DEFAULT_CHROMA_PERSIST_DIRECTORY
            ),
            embedding_model=_read_text("EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL),
            embedding_device=_read_text("EMBEDDING_DEVICE", DEFAULT_EMBEDDING_DEVICE),
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide settings instance."""
    return Settings.from_env()
