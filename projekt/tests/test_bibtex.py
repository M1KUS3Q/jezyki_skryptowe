"""Unit tests for BibTeX citation generation."""

import pytest

from paper_aggregator.domain.bibtex import (
    _first_title_word,
    _last_name,
    format_bibtex,
    generate_citation_key,
)


class TestLastName:
    def test_simple(self) -> None:
        assert _last_name("Vaswani, Ashish") == "Vaswani"

    def test_compound_last_name(self) -> None:
        assert _last_name("von Neumann, John") == "von Neumann"

    def test_no_comma(self) -> None:
        assert _last_name("Doe") == "Doe"


class TestFirstTitleWord:
    def test_normal_title(self) -> None:
        assert _first_title_word("Attention Is All You Need") == "attention"

    def test_title_starts_with_stopword(self) -> None:
        assert _first_title_word("The Theory of Everything") == "theory"

    def test_all_stopwords(self) -> None:
        assert _first_title_word("The A An") == "the"

    def test_empty_title(self) -> None:
        assert _first_title_word("") == "untitled"

    def test_title_with_punctuation(self) -> None:
        assert _first_title_word("Deep Learning: A Survey") == "deep"

    def test_numbers_in_title(self) -> None:
        assert _first_title_word("BERT: Pre-training of Deep Bidirectional Transformers") == "bert"


class TestCitationKey:
    def test_standard(self) -> None:
        key = generate_citation_key(
            "Vaswani, Ashish, Shazeer, Noam", 2017, "Attention Is All You Need"
        )
        assert key == "vaswani2017attention"

    def test_null_year(self) -> None:
        key = generate_citation_key("Doe, John", None, "Some Paper About Stuff")
        assert key == "doeXXXXsome"

    def test_compound_last_name(self) -> None:
        key = generate_citation_key(
            "von Neumann, John", 1955, "Mathematical Foundations"
        )
        assert key == "vonneumann1955mathematical"

    def test_accented_name(self) -> None:
        key = generate_citation_key(
            "Gödel, Kurt", 1931, "Über formal unentscheidbare Sätze"
        )
        assert key == "godel1931uber"

    def test_title_all_stopwords(self) -> None:
        key = generate_citation_key("Smith, Alice", 2020, "The And Or")
        assert key == "smith2020the"

    def test_spaces_in_name(self) -> None:
        key = generate_citation_key("  Vaswani,  Ashish  ", 2017, "Attention Is All You Need")
        assert key == "vaswani2017attention"


class TestFormatBibtex:
    def test_full_entry(self) -> None:
        paper = {
            "title": "Attention Is All You Need",
            "authors": "Vaswani, Ashish, Shazeer, Noam",
            "year": 2017,
            "url": "https://arxiv.org/abs/1706.03762",
            "abstract_summary": "We propose the Transformer, a novel architecture.",
        }
        result = format_bibtex(paper)

        assert result.startswith("@article{vaswani2017attention,")
        assert "author = {Vaswani, Ashish and Shazeer, Noam}," in result
        assert "title = {Attention Is All You Need}," in result
        assert "year = {2017}," in result
        assert "url = {https://arxiv.org/abs/1706.03762}," in result
        assert "note = {We propose the Transformer, a novel architecture.}," in result

    def test_inproceedings_type(self) -> None:
        paper = {
            "title": "A New Approach",
            "authors": "Doe, John",
            "year": 2023,
            "url": "",
            "abstract_summary": "",
        }
        result = format_bibtex(paper, entry_type="inproceedings")
        assert result.startswith("@inproceedings{doe2023new,")

    def test_no_year(self) -> None:
        paper = {
            "title": "Untitled",
            "authors": "Doe, John",
            "year": None,
            "url": "",
            "abstract_summary": "",
        }
        result = format_bibtex(paper)
        assert "XXXX" in result
        assert "year =" not in result  # Not present when None

    def test_truncates_long_abstract(self) -> None:
        paper = {
            "title": "T",
            "authors": "A, B",
            "year": 2024,
            "url": "",
            "abstract_summary": "X" * 400,
        }
        result = format_bibtex(paper)
        # Should be truncated to 300 chars + "..."
        assert "..." in result
        # The note shouldn't be 400 chars
        note_line = [l for l in result.splitlines() if "note" in l][0]
        assert len(note_line) < 350

    def test_no_url_no_note(self) -> None:
        paper = {
            "title": "Minimal Paper",
            "authors": "Someone, Some",
            "year": 2020,
            "url": "",
            "abstract_summary": "",
        }
        result = format_bibtex(paper)
        assert "url =" not in result
        assert "note =" not in result
