"""Unit tests for search filter parsing and building."""

from paper_aggregator.domain.search import (
    SearchFilters,
    build_search_filters,
    parse_year_filter,
)


class TestParseYearFilter:
    """T1.7 — year filter parsing."""

    def test_single_year(self) -> None:
        assert parse_year_filter("2020") == (2020, 2020)

    def test_year_range(self) -> None:
        assert parse_year_filter("2020-2023") == (2020, 2023)

    def test_year_range_with_spaces(self) -> None:
        assert parse_year_filter(" 2019 - 2022 ") == (2019, 2022)

    def test_invalid_range_reversed(self) -> None:
        assert parse_year_filter("2023-2020") == (None, None)

    def test_garbage_input(self) -> None:
        assert parse_year_filter("not-a-year") == (None, None)

    def test_empty_string(self) -> None:
        assert parse_year_filter("") == (None, None)

    def test_partial_range(self) -> None:
        assert parse_year_filter("2020-") == (None, None)

    def test_three_part_range(self) -> None:
        # Only the first '-' is treated as separator; second part is not a digit.
        assert parse_year_filter("2020-2021-2022") == (None, None)


class TestBuildSearchFilters:
    """T1.7 — filter assembly from CLI inputs."""

    def test_empty_filters(self) -> None:
        f = build_search_filters()
        assert f.tags is None
        assert f.author is None
        assert f.field is None
        assert f.year_from is None
        assert f.limit == 50

    def test_tags_passed_through(self) -> None:
        f = build_search_filters(tags=["transformers", "attention"])
        assert f.tags == ["transformers", "attention"]

    def test_author_trimmed(self) -> None:
        f = build_search_filters(author="  Vaswani  ")
        assert f.author == "Vaswani"

    def test_author_none_when_empty_or_whitespace(self) -> None:
        f = build_search_filters(author="   ")
        assert f.author is None

    def test_exact_year(self) -> None:
        f = build_search_filters(year="2023")
        assert f.year_exact == 2023
        assert f.year_from == 2023
        assert f.year_to == 2023

    def test_year_range(self) -> None:
        f = build_search_filters(year="2018-2022")
        assert f.year_exact is None
        assert f.year_from == 2018
        assert f.year_to == 2022

    def test_custom_limit(self) -> None:
        f = build_search_filters(limit=10)
        assert f.limit == 10

    def test_empty_tags_list_yields_none(self) -> None:
        f = build_search_filters(tags=[])
        assert f.tags is None

    def test_all_filters_combined(self) -> None:
        f = build_search_filters(
            tags=["nlp"],
            author="Smith",
            field="CS",
            year="2020-2024",
            limit=25,
        )
        assert f.tags == ["nlp"]
        assert f.author == "Smith"
        assert f.field == "CS"
        assert f.year_from == 2020
        assert f.year_to == 2024
        assert f.limit == 25
