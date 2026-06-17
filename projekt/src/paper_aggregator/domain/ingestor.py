"""Paper ingestion - URL validation, download, and PDF text extraction."""

from __future__ import annotations

import hashlib
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import fitz  # PyMuPDF
import httpx

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


def download_pdf(url: str, dest_path: Path) -> tuple[str, str | None]:
    """Download a file from *url* into *dest_path*.

    Returns a ``(content_hash, content_type)`` tuple — *content_type* is
    the value of the ``Content-Type`` response header (may be ``None``).

    Raises :class:`httpx.HTTPStatusError` when the response status is not 2xx,
    and :class:`httpx.RequestError` for network-level failures.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; paper-aggregator/0.1; "
            "+https://github.com/paper-aggregator)"
        ),
    }
    with httpx.Client(
        follow_redirects=True, timeout=30.0, headers=headers
    ) as client:
        response = client.get(url)
        response.raise_for_status()

        dest_path.parent.mkdir(parents=True, exist_ok=True)
        dest_path.write_bytes(response.content)

        content_type: str | None = response.headers.get("Content-Type")

    return compute_content_hash(dest_path), content_type


def extract_text(pdf_path: Path) -> str:
    """Extract plain text from a PDF file using PyMuPDF.

    Returns the concatenated text from all pages.

    Raises :class:`ValueError` if the PDF is encrypted or yields no text.
    """
    try:
        doc = fitz.open(pdf_path)
    except (fitz.FileDataError, RuntimeError) as exc:
        raise ValueError(
            f"Cannot open PDF file: {pdf_path}. The file may be corrupted "
            f"or not a valid PDF. ({exc})"
        ) from exc

    if doc.is_encrypted:
        doc.close()
        raise ValueError(
            f"Cannot extract text from encrypted PDF: {pdf_path}. "
            f"Password-protected PDFs are not supported."
        )

    pages: list[str] = []
    for page in doc:
        pages.append(page.get_text())

    doc.close()

    text = "\n".join(pages)
    if not text.strip():
        raise ValueError(
            f"No extractable text found in PDF: {pdf_path}. "
            f"The file may be scanned images only."
        )

    return text


def compute_content_hash(file_path: Path) -> str:
    """Return the SHA-256 hash of a file's contents."""
    sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha.update(chunk)
    return sha.hexdigest()
