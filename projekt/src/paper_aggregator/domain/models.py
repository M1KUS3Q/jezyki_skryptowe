"""Pydantic models for LLM tagging response validation.

Corresponds to the tagging schema defined in REQUIREMENTS.md §3.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class PaperTags(BaseModel):
    """Structured tags returned by the LLM for a single paper."""

    title: str
    authors: list[str]
    year: int | None = None
    primary_field: str
    sub_field: str | None = None
    keywords: list[str] = Field(min_length=1, max_length=8)
    methodology: list[str]
    abstract_summary: str
