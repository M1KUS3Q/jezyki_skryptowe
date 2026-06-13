"""Paper ingestion - URL validation, download, and PDF text extraction."""

from __future__ import annotations

import hashlib
import tempfile
from pathlib import Path


def validate_url(url: str) -> bool:
    """Check that a URL is well-formed."""
    ...


def detect_file_type(content_type: str | None, url: str) -> str:
    """Determine file type from Content-Type header or URL extension."""
    ...


def download_pdf(url: str, dest_path: Path) -> str:
    """Download a PDF from *url* into *dest_path*.

    Returns the SHA-256 content hash of the downloaded file.
    """
    ...


def extract_text(pdf_path: Path) -> str:
    """Extract plain text from a PDF file using PyMuPDF."""
    ...


def compute_content_hash(file_path: Path) -> str:
    """Return the SHA-256 hash of a file's contents."""
    sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha.update(chunk)
    return sha.hexdigest()
