"""Configuration loading and validation tests."""

import pytest

from university_knowledge_assistant.config import (
    DEFAULT_LLM_MODEL,
    Settings,
    get_settings,
)

_ENV_NAMES = [
    "LLM_BASE_URL",
    "LLM_MODEL",
    "LLM_API_KEY",
    "LLM_TEMPERATURE",
    "LLM_MAX_TOKENS",
    "LLM_TIMEOUT_SECONDS",
    "RETRIEVAL_TOP_K",
    "CHROMA_PERSIST_DIRECTORY",
    "EMBEDDING_MODEL",
    "EMBEDDING_DEVICE",
]


@pytest.fixture(autouse=True)
def _clean_environment(monkeypatch):
    for name in _ENV_NAMES:
        monkeypatch.delenv(name, raising=False)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_default_settings_are_sensible() -> None:
    settings = Settings.from_env()

    assert settings.llm_base_url == "http://localhost:1234/v1"
    assert settings.llm_model == DEFAULT_LLM_MODEL == "qwen3.5-9b"
    assert settings.llm_api_key == "lm-studio"
    assert settings.llm_max_tokens == 2048
    assert settings.retrieval_top_k == 3
    assert settings.embedding_device == "cpu"


def test_environment_overrides_defaults(monkeypatch) -> None:
    monkeypatch.setenv("LLM_BASE_URL", "http://example.local:1234/v1/")
    monkeypatch.setenv("LLM_MODEL", "other-model")
    monkeypatch.setenv("LLM_TEMPERATURE", "0.9")
    monkeypatch.setenv("LLM_MAX_TOKENS", "256")
    monkeypatch.setenv("RETRIEVAL_TOP_K", "5")

    settings = Settings.from_env()

    assert settings.llm_base_url == "http://example.local:1234/v1/"
    assert settings.llm_model == "other-model"
    assert settings.llm_temperature == 0.9
    assert settings.llm_max_tokens == 256
    assert settings.retrieval_top_k == 5


def test_get_settings_is_cached(monkeypatch) -> None:
    monkeypatch.setenv("LLM_MODEL", "first")

    first = get_settings()
    monkeypatch.setenv("LLM_MODEL", "second")

    assert get_settings() is first
    assert first.llm_model == "first"


def test_invalid_numeric_environment_variable(monkeypatch) -> None:
    monkeypatch.setenv("LLM_TEMPERATURE", "hot")

    with pytest.raises(ValueError, match="LLM_TEMPERATURE must be a number"):
        Settings.from_env()


@pytest.mark.parametrize(
    "overrides",
    [
        {"llm_base_url": "localhost:1234/v1"},
        {"llm_model": ""},
        {"llm_temperature": -0.1},
        {"llm_temperature": 2.1},
        {"llm_max_tokens": 0},
        {"retrieval_top_k": 0},
        {"chroma_persist_directory": ""},
    ],
)
def test_invalid_settings_are_rejected(overrides: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        Settings(**overrides)  # type: ignore[arg-type]
