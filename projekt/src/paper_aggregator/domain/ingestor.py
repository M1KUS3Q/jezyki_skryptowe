"""Paper ingestion - URL validation, download, and PDF text extraction."""

from __future__ import annotations

import hashlib
import tempfile
from pathlib import Path
from urllib.parse import urlparse

# Maps Content-Type header values (or prefixes) to internal file-type labels.
_CONTENT_TYPE_MAP: dict[str, str] = {
    "application/pdf": "pdf",
    "text/plain": "txt",
}

# Maps file extensions (lowercase, with leading dot) to internal file-type labels.
_EXTENSION_MAP: dict[str, str] = {
    ".pdf": "pdf",
    ".txt": "txt",
}


def validate_url(url: str) -> bool:
    """Check that a URL is well-formed and has an http/https scheme."""
    try:
        parsed = urlparse(url)
    except (ValueError, AttributeError):
        return False

    if parsed.scheme not in ("http", "https"):
        return False

    return bool(parsed.netloc)


def detect_file_type(content_type: str | None, url: str) -> str:
    """Determine file type from Content-Type header or URL extension.

    Returns one of ``"pdf"``, ``"txt"``, or raises :class:`ValueError` for
    unsupported formats.
    """
    # Content-Type header takes precedence.
    if content_type:
        for key, file_type in _CONTENT_TYPE_MAP.items():
            if content_type.lower().startswith(key):
                return file_type

    # Fall back to extension from the URL path.
    path = urlparse(url).path
    suffix = Path(path).suffix.lower()
    if suffix in _EXTENSION_MAP:
        return _EXTENSION_MAP[suffix]

    raise ValueError(
        f"Unsupported file type (Content-Type={content_type!r}, "
        f"extension={suffix!r}). Only PDF and plain-text files are supported."
    )


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
