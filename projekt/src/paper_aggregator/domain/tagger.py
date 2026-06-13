"""LLM tagging - send extracted text to the LLM and parse the response."""

from __future__ import annotations

from paper_aggregator.domain.models import PaperTags


def truncate_text(text: str, max_chars: int) -> tuple[str, bool]:
    """Truncate *text* to *max_chars* characters.

    Returns (truncated_text, was_truncated).
    """
    if len(text) <= max_chars:
        return text, False
    return text[:max_chars], True


def tag_paper(text: str, model: str | None = None) -> PaperTags:
    """Send paper text to the LLM and return validated tags."""
    ...


def build_tagging_prompt(text: str) -> str:
    """Build the prompt that instructs the LLM to tag a paper."""
    ...
