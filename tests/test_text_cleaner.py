"""Tests for conservative whitespace normalization."""

import pytest

from university_knowledge_assistant.preprocessing import clean_text


def test_clean_text_collapses_spaces_and_blank_lines() -> None:
    raw = "Hello   world\n\n\n\nSecond   line."

    assert clean_text(raw) == "Hello world\n\nSecond line."


def test_clean_text_preserves_punctuation_and_case() -> None:
    raw = "ReLU(x) = max(0, x)!  Keep 2.5% and A <= B."

    assert clean_text(raw) == "ReLU(x) = max(0, x)! Keep 2.5% and A <= B."


def test_clean_text_keeps_code_indentation() -> None:
    raw = "def loss(y, p):\n\treturn  -(y * log(p)).mean()"

    assert clean_text(raw) == "def loss(y, p):\n\treturn -(y * log(p)).mean()"


def test_clean_text_handles_windows_line_endings_and_empty_text() -> None:
    assert clean_text("A\r\n\r\n\r\nB") == "A\n\nB"
    assert clean_text("") == ""
    assert clean_text("   \n\n  ") == ""


def test_clean_text_rejects_non_string_input() -> None:
    with pytest.raises(TypeError):
        clean_text(None)  # type: ignore[arg-type]
