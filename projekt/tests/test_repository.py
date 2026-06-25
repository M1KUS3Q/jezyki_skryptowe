"""Integration tests for PaperRepository - CRUD, search, and tag management.

These tests use a temporary on-disk SQLite database so foreign-key pragmas
and WAL mode work identically to the production path.
"""

import sqlite3

import pytest

from paper_aggregator.db.repository import PaperRepository


def _add_sample_paper(repo: PaperRepository, url: str, title: str = "Test Paper") -> int:
    """Helper: add a fully-metadata'd paper and return its ID."""
    pid = repo.add_paper(url, f"/tmp/{title.replace(' ', '_')}.pdf", "abc123")
    repo.save_paper_metadata(
        paper_id=pid,
        title=title,
        authors=["Doe, John", "Smith, Jane"],
        year=2024,
        primary_field="Computer Science",
        sub_field="Machine Learning",
        keywords=["transformers", "attention"],
        methodology=["deep learning"],
        abstract_summary="A test paper.",
    )
    return pid


class TestPaperExists:
    """T1.5 - deduplication checks."""

    def test_new_url_does_not_exist(self, db_repo: PaperRepository) -> None:
        assert db_repo.paper_exists("https://example.com/new.pdf") is False

    def test_existing_url_is_found(self, db_repo: PaperRepository) -> None:
        db_repo.add_paper("https://example.com/paper.pdf", "/tmp/p.pdf")
        assert db_repo.paper_exists("https://example.com/paper.pdf") is True

    def test_duplicate_url_raises_integrity_error(self, db_repo: PaperRepository) -> None:
        db_repo.add_paper("https://example.com/dup.pdf", "/tmp/dup.pdf")
        with pytest.raises(sqlite3.IntegrityError):
            db_repo.add_paper("https://example.com/dup.pdf", "/tmp/dup2.pdf")


class TestAddAndRetrieve:
    """T1.9 - basic CRUD."""

    def test_add_paper_returns_valid_id(self, db_repo: PaperRepository) -> None:
        pid = _add_sample_paper(db_repo, "https://example.com/1.pdf")
        assert isinstance(pid, int)
        assert pid > 0

    def test_get_paper_returns_full_details(self, db_repo: PaperRepository) -> None:
        pid = _add_sample_paper(db_repo, "https://example.com/2.pdf")
        paper = db_repo.get_paper(pid)
        assert paper is not None
        assert paper["title"] == "Test Paper"
        assert paper["year"] == 2024
        assert "Doe, John" in paper["authors"]
        assert "transformers" in paper["keywords"]
        assert "deep learning" in paper["methodology"]

    def test_get_paper_nonexistent(self, db_repo: PaperRepository) -> None:
        assert db_repo.get_paper(9999) is None

    def test_get_paper_by_url(self, db_repo: PaperRepository) -> None:
        _add_sample_paper(db_repo, "https://example.com/3.pdf", "URL Paper")
        paper = db_repo.get_paper_by_url("https://example.com/3.pdf")
        assert paper is not None
        assert paper["title"] == "URL Paper"


class TestRemove:
    """T1.9 - remove operations."""

    def test_remove_existing_paper(self, db_repo: PaperRepository) -> None:
        pid = _add_sample_paper(db_repo, "https://example.com/to-remove.pdf")
        assert db_repo.remove_paper(pid) is True
        assert db_repo.get_paper(pid) is None

    def test_remove_nonexistent_paper(self, db_repo: PaperRepository) -> None:
        assert db_repo.remove_paper(9999) is False

    def test_remove_by_url(self, db_repo: PaperRepository) -> None:
        _add_sample_paper(db_repo, "https://example.com/rm-url.pdf")
        assert db_repo.remove_paper_by_url("https://example.com/rm-url.pdf") is True
        assert db_repo.get_paper_by_url("https://example.com/rm-url.pdf") is None


class TestListAll:
    """T1.9 - listing."""

    def test_list_returns_newest_first(self, db_repo: PaperRepository) -> None:
        _add_sample_paper(db_repo, "https://example.com/old.pdf", "Old Paper")
        _add_sample_paper(db_repo, "https://example.com/new.pdf", "New Paper")
        results = db_repo.list_all()
        assert results[0]["title"] == "New Paper"  # newest first

    def test_list_with_tag_filter(self, db_repo: PaperRepository) -> None:
        _add_sample_paper(db_repo, "https://example.com/tagged.pdf", "Tagged Paper")
        results = db_repo.list_all(tag="transformers")
        assert len(results) >= 1
        assert any(r["title"] == "Tagged Paper" for r in results)

    def test_list_with_nonexistent_tag(self, db_repo: PaperRepository) -> None:
        _add_sample_paper(db_repo, "https://example.com/no-tag.pdf")
        results = db_repo.list_all(tag="nonexistent-tag-xyz")
        assert len(results) == 0

    def test_list_respects_limit(self, db_repo: PaperRepository) -> None:
        for i in range(5):
            _add_sample_paper(db_repo, f"https://example.com/{i}.pdf", f"Paper {i}")
        results = db_repo.list_all(limit=2)
        assert len(results) == 2


class TestSearch:
    """T1.7 - search query building."""

    def test_search_by_single_tag(self, db_repo: PaperRepository) -> None:
        _add_sample_paper(db_repo, "https://example.com/s1.pdf", "NLP Paper")
        results = db_repo.search_papers(tags=["transformers"])
        assert len(results) >= 1
        assert any("NLP Paper" == r["title"] for r in results)

    def test_search_by_multiple_tags_and(self, db_repo: PaperRepository) -> None:
        pid = db_repo.add_paper("https://example.com/s2.pdf", "/tmp/s2.pdf", "hash2")
        db_repo.save_paper_metadata(
            paper_id=pid,
            title="Multi-tag Paper",
            authors=["Doe, John"],
            year=2023,
            primary_field="CS",
            sub_field="NLP",
            keywords=["transformers", "attention"],
            methodology=["deep learning"],
            abstract_summary="Both tags.",
        )
        # Paper has both tags -> should match AND
        results = db_repo.search_papers(tags=["transformers", "attention"])
        assert any("Multi-tag Paper" == r["title"] for r in results)

    def test_search_by_author_substring(self, db_repo: PaperRepository) -> None:
        _add_sample_paper(db_repo, "https://example.com/author.pdf")
        results = db_repo.search_papers(author="Doe")
        assert len(results) >= 1

    def test_search_by_author_case_insensitive(self, db_repo: PaperRepository) -> None:
        _add_sample_paper(db_repo, "https://example.com/case.pdf")
        results = db_repo.search_papers(author="doe")  # lowercase
        assert len(results) >= 1

    def test_search_by_field(self, db_repo: PaperRepository) -> None:
        _add_sample_paper(db_repo, "https://example.com/field.pdf")
        results = db_repo.search_papers(field="Computer")
        assert len(results) >= 1

    def test_search_by_year_exact(self, db_repo: PaperRepository) -> None:
        _add_sample_paper(db_repo, "https://example.com/year.pdf")
        results = db_repo.search_papers(year="2024")
        assert len(results) >= 1
        assert all(r["year"] == 2024 for r in results)

    def test_search_no_results(self, db_repo: PaperRepository) -> None:
        results = db_repo.search_papers(tags=["no-such-tag-xyz"])
        assert len(results) == 0


class TestListTags:
    """T1.9 - tag listing with counts."""

    def test_tags_with_counts(self, db_repo: PaperRepository) -> None:
        _add_sample_paper(db_repo, "https://example.com/tags1.pdf")
        _add_sample_paper(db_repo, "https://example.com/tags2.pdf")
        tags = db_repo.list_tags()
        assert len(tags) > 0
        # "transformers" appears in both papers
        tf_row = next(t for t in tags if t["name"] == "transformers")
        assert tf_row["paper_count"] >= 1
        assert tf_row["category"] == "keyword"

    def test_tags_empty_db(self, db_repo: PaperRepository) -> None:
        tags = db_repo.list_tags()
        assert tags == []
