"""Shared fixtures for the paper-aggregator test suite."""

import os
from pathlib import Path
from unittest.mock import MagicMock

import fitz
import pytest

from paper_aggregator.domain.models import PaperTags


# ---------------------------------------------------------------------------
# PDF fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def sample_pdf_path(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A valid single-page PDF containing readable text."""
    p = tmp_path_factory.mktemp("pdfs") / "sample.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(
        (72, 72),
        "This is a test paper about machine learning and transformers. "
        "Authors: John Doe, Jane Smith. "
        "Abstract: We propose a novel approach to attention mechanisms.",
    )
    doc.save(str(p))
    doc.close()
    return p


@pytest.fixture(scope="session")
def encrypted_pdf_path(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A password-protected PDF."""
    p = tmp_path_factory.mktemp("pdfs") / "encrypted.pdf"
    doc = fitz.open()
    doc.new_page().insert_text((72, 72), "Secret content")
    doc.save(
        str(p),
        encryption=fitz.PDF_ENCRYPT_AES_256,
        owner_pw="secret",
        user_pw="secret",
    )
    doc.close()
    return p


@pytest.fixture(scope="session")
def empty_pdf_path(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A PDF with a blank page (no extractable text)."""
    p = tmp_path_factory.mktemp("pdfs") / "empty.pdf"
    doc = fitz.open()
    doc.new_page()
    doc.save(str(p))
    doc.close()
    return p


# ---------------------------------------------------------------------------
# LLM / tag fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def sample_paper_tags() -> PaperTags:
    """A valid PaperTags instance used across tagger and repository tests."""
    return PaperTags(
        title="Test Paper Title",
        authors=["Doe, John", "Smith, Jane"],
        year=2024,
        primary_field="Computer Science",
        sub_field="Machine Learning",
        keywords=["transformers", "attention"],
        methodology=["deep learning"],
        abstract_summary="A test paper about testing.",
    )


@pytest.fixture
def mock_openai_client(sample_paper_tags: PaperTags) -> MagicMock:
    """A MagicMock that behaves like an OpenAI client and returns valid tags."""
    import json

    client = MagicMock()
    choice = MagicMock()
    choice.message.content = sample_paper_tags.model_dump_json()
    client.chat.completions.create.return_value = MagicMock(choices=[choice])
    return client


# ---------------------------------------------------------------------------
# DB fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def db_repo(tmp_path: Path) -> "PaperRepository":
    """A PaperRepository backed by a temporary on-disk SQLite database."""
    from paper_aggregator.db.repository import PaperRepository

    repo = PaperRepository(tmp_path / "test.db")
    repo.initialize()
    return repo
