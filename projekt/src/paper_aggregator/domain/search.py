"""Search logic - build SQL queries from user-provided filters."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SearchFilters:
    """Structured representation of user search filters."""

    tags: list[str] | None = None
    author: str | None = None
    field: str | None = None
    year_exact: int | None = None
    year_from: int | None = None
    year_to: int | None = None
    limit: int = 50


def parse_year_filter(year_spec: str) -> tuple[int | None, int | None]:
    """Parse a year filter string.

    ``"2020"`` → (2020, 2020)
    ``"2020-2023"`` → (2020, 2023)
    """
    ...


def build_search_filters(
    tags: list[str] | None = None,
    author: str | None = None,
    field: str | None = None,
    year: str | None = None,
    limit: int = 50,
) -> SearchFilters:
    """Build a SearchFilters instance from raw CLI inputs."""
    ...
