"""Conservative text cleaning for text extracted from PDFs.

The goal is to remove layout noise (repeated spaces and excessive blank
lines) without changing the content. We deliberately do **not** lowercase,
remove punctuation, stem words or strip symbols: course material often
contains formulas, code and technical notation where those transformations
would destroy meaning.
"""

import re

# Keep at most one empty line between paragraphs.
_MAX_CONSECUTIVE_BLANK_LINES = 1


def _normalize_line(line: str) -> str:
    """Collapse repeated spaces inside a line while preserving indentation."""
    leading_length = len(line) - len(line.lstrip(" \t"))
    leading = line[:leading_length]
    body = re.sub(r" {2,}", " ", line[leading_length:]).rstrip()
    return leading + body if body else ""


def clean_text(text: str) -> str:
    """Normalize whitespace in extracted text without altering its content.

    Args:
        text: Raw text extracted from a PDF page.

    Returns:
        Text with normalized line endings, repeated spaces collapsed and at
        most one blank line between paragraphs.

    Raises:
        TypeError: If ``text`` is not a string.
    """
    if not isinstance(text, str):
        raise TypeError(f"text must be a string, got {type(text).__name__}")

    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    output: list[str] = []
    blank_lines = 0

    for line in normalized.split("\n"):
        cleaned_line = _normalize_line(line)
        if cleaned_line:
            output.append(cleaned_line)
            blank_lines = 0
        elif blank_lines < _MAX_CONSECUTIVE_BLANK_LINES:
            output.append("")
            blank_lines += 1

    return "\n".join(output).strip()
