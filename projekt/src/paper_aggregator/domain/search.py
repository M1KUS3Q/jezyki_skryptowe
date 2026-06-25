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

    ``"2020"`` -> ``(2020, 2020)``
    ``"2020-2023"`` -> ``(2020, 2023)``

    Returns ``(None, None)`` for any input that cannot be parsed as a
    valid year or year range.
    """
    spec = year_spec.strip()

    # Single year: "YYYY"
    if spec.isdigit():
        year = int(spec)
        return (year, year)

    # Range: "YYYY-YYYY"
    if "-" in spec:
        parts = spec.split("-", 1)
        if len(parts) == 2 and parts[0].strip().isdigit() and parts[1].strip().isdigit():
            y_from = int(parts[0].strip())
            y_to = int(parts[1].strip())
            if y_from <= y_to:
                return (y_from, y_to)

    return (None, None)


def build_search_filters(
    tags: list[str] | None = None,
    author: str | None = None,
    field: str | None = None,
    year: str | None = None,
    limit: int = 50,
) -> SearchFilters:
    """Build a :class:`SearchFilters` instance from raw CLI inputs.

    Parameters
    ----------
    tags:
        List of tag names to filter by (AND semantics).
    author:
        Substring to match against author names.
    field:
        Substring to match against ``primary_field`` or ``sub_field``.
    year:
        Year specification (``"YYYY"`` or ``"YYYY-YYYY"``).
    limit:
        Maximum number of results to return.
    """
    year_from: int | None = None
    year_to: int | None = None

    if year is not None:
        year_from, year_to = parse_year_filter(year)

    author_clean = author.strip() if author else ""
    field_clean = field.strip() if field else ""

    return SearchFilters(
        tags=tags if tags else None,
        author=author_clean or None,
        field=field_clean or None,
        year_exact=None if year_from != year_to or year_from is None else year_from,
        year_from=year_from,
        year_to=year_to,
        limit=limit,
    )
