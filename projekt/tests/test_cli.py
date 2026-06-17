"""CLI-level tests using Typer's CliRunner.

These mock the LLM layer so no API key is required.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import fitz
import pytest
from typer.testing import CliRunner

from paper_aggregator.cli.commands import app
from paper_aggregator.domain.models import PaperTags


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def sample_pdf(tmp_path: Path) -> Path:
    """A small valid PDF for CLI testing."""
    p = tmp_path / "cli_test.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(
        (72, 72),
        "Machine Learning for Healthcare\n\n"
        "Authors: Alice Johnson, Bob Lee\n\n"
        "Abstract: We apply deep learning to electronic health records "
        "for early detection of sepsis. Our LSTM-based model achieves "
        "0.95 AUC on the MIMIC-III benchmark.\n\n"
        "1. Introduction\n"
        "Early detection of sepsis is critical...",
    )
    doc.save(str(p))
    doc.close()
    return p


@pytest.fixture
def mock_tags() -> PaperTags:
    return PaperTags(
        title="Machine Learning for Healthcare",
        authors=["Johnson, Alice", "Lee, Bob"],
        year=2023,
        primary_field="Computer Science",
        sub_field="Medical Informatics",
        keywords=["deep learning", "healthcare", "sepsis", "LSTM"],
        methodology=["deep learning", "LSTM"],
        abstract_summary="Deep learning applied to EHR for sepsis detection.",
    )


class TestAddLocalFile:
    """Exercise the local-file path through the full CLI ``add`` command."""

    def test_dry_run_local_pdf(
        self, runner: CliRunner, sample_pdf: Path, mock_tags: PaperTags
    ) -> None:
        """``add --dry-run`` with a local PDF should print tags but not write DB."""
        with patch(
            "paper_aggregator.cli.commands.tag_paper",
            return_value=mock_tags,
        ) as mock_tag:
            result = runner.invoke(
                app,
                ["add", str(sample_pdf), "--dry-run"],
                catch_exceptions=False,
            )

        assert result.exit_code == 0, f"stderr: {result.stderr}"
        assert "Using local file" in result.stdout
        assert "Tagged" in result.stdout
        assert mock_tags.title in result.stdout
        # Should NOT write to DB.
        assert "Stored in database" not in result.stdout

    def test_add_local_pdf_writes_to_db(
        self,
        runner: CliRunner,
        sample_pdf: Path,
        mock_tags: PaperTags,
        tmp_path: Path,
    ) -> None:
        """``add`` with a local PDF should store the paper in the database."""
        # Point the DB at a temp location so we don't touch the real one.
        db_path = tmp_path / "test_cli.db"

        with patch(
            "paper_aggregator.cli.commands.app_settings.db_path", db_path
        ), patch(
            "paper_aggregator.cli.commands.app_settings.pdf_storage_path",
            tmp_path / "pdfs",
        ), patch(
            "paper_aggregator.cli.commands.tag_paper",
            return_value=mock_tags,
        ):
            result = runner.invoke(
                app,
                ["add", str(sample_pdf)],
                catch_exceptions=False,
            )

        assert result.exit_code == 0, f"stderr: {result.stderr}"
        assert "Using local file" in result.stdout
        assert "Tagged" in result.stdout
        assert "Stored in database" in result.stdout
        assert "PDF copied to" in result.stdout

        # Verify it's in the DB.
        from paper_aggregator.db.repository import PaperRepository

        repo = PaperRepository(db_path)
        repo.initialize()
        papers = repo.list_all()
        assert len(papers) == 1
        assert papers[0]["title"] == mock_tags.title
        # file:// URI should be the canonical URL.
        assert papers[0]["url"].startswith("file://")

    def test_add_local_file_invalid_extension(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        """A local file with an unsupported extension should be rejected."""
        bad = tmp_path / "image.png"
        bad.write_bytes(b"\x89PNG\r\n\x1a\n")
        result = runner.invoke(app, ["add", str(bad)])
        assert "Unsupported file type" in result.stdout

    def test_add_nonexistent_local_path(self, runner: CliRunner) -> None:
        """A path that doesn't exist on disk should fail validation."""
        result = runner.invoke(app, ["add", "/tmp/nonexistent-file-12345.pdf"])
        assert "Invalid URL or non-existent file" in result.stdout


class TestAddRemoteURL:
    """Exercise the remote-URL path with a mocked download."""

    def test_add_url_dry_run(
        self, runner: CliRunner, mock_tags: PaperTags, tmp_path: Path
    ) -> None:
        """``add --dry-run <url>`` should download, tag, and print without DB."""
        # Create a tiny "downloaded PDF".
        pdf_bytes = b"fake-pdf-content"
        mock_response = MagicMock()
        mock_response.headers.get.return_value = "application/pdf"
        mock_response.content = pdf_bytes
        mock_response.raise_for_status.return_value = None

        with patch(
            "paper_aggregator.cli.commands.tag_paper",
            return_value=mock_tags,
        ), patch(
            "paper_aggregator.cli.commands.download_pdf",
            return_value=("abc123hash", "application/pdf"),
        ), patch(
            "paper_aggregator.cli.commands.extract_text",
            return_value="test paper text content for tagging",
        ), patch(
            "paper_aggregator.cli.commands.app_settings.db_path",
            tmp_path / "test.db",
        ), patch(
            "paper_aggregator.cli.commands.app_settings.pdf_storage_path",
            tmp_path / "pdfs",
        ):
            result = runner.invoke(
                app,
                ["add", "https://example.com/paper.pdf", "--dry-run"],
                catch_exceptions=False,
            )

        assert result.exit_code == 0, f"stderr: {result.stderr}"
        assert "Downloaded" in result.stdout
        assert "Tagged" in result.stdout
        assert mock_tags.title in result.stdout
        assert "Stored in database" not in result.stdout
