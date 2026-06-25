"""Unit tests for paper ingestion - URL validation, file-type detection,
and PDF text extraction."""

import pytest

from paper_aggregator.domain.ingestor import (
    detect_file_type,
    extract_text,
    validate_url,
)


class TestValidateURL:
    """F1.2 / T1.1 - URL validation."""

    def test_valid_https_url(self) -> None:
        assert validate_url("https://example.com/paper.pdf") is True

    def test_valid_http_url(self) -> None:
        assert validate_url("http://arxiv.org/abs/1234.5678") is True

    def test_url_with_query_params(self) -> None:
        assert validate_url("https://example.com/dl?doi=10.1234&format=pdf") is True

    def test_rejects_ftp_scheme(self) -> None:
        assert validate_url("ftp://files.example.com/paper.pdf") is False

    def test_rejects_empty_string(self) -> None:
        assert validate_url("") is False

    def test_rejects_gibberish(self) -> None:
        assert validate_url("not-a-url") is False

    def test_rejects_missing_netloc(self) -> None:
        assert validate_url("https:///path/only") is False

    def test_rejects_no_scheme(self) -> None:
        assert validate_url("example.com/file.pdf") is False


class TestDetectFileType:
    """T1.6 - file-type detection from Content-Type and extension."""

    def test_pdf_from_content_type(self) -> None:
        assert detect_file_type("application/pdf", "https://example.com/file") == "pdf"

    def test_pdf_content_type_with_charset(self) -> None:
        assert detect_file_type("application/pdf; charset=utf-8", "https://example.com/file") == "pdf"

    def test_txt_from_content_type(self) -> None:
        assert detect_file_type("text/plain", "https://example.com/file") == "txt"

    def test_pdf_from_extension(self) -> None:
        assert detect_file_type(None, "https://example.com/paper.pdf") == "pdf"

    def test_txt_from_extension(self) -> None:
        assert detect_file_type(None, "https://example.com/notes.txt") == "txt"

    def test_content_type_takes_precedence(self) -> None:
        # Content-Type says PDF even though the extension is .txt
        assert detect_file_type("application/pdf", "https://example.com/file.txt") == "pdf"

    def test_unsupported_content_type_with_no_extension(self) -> None:
        with pytest.raises(ValueError, match="Unsupported file type"):
            detect_file_type("image/png", "https://example.com/file")

    def test_unsupported_extension(self) -> None:
        with pytest.raises(ValueError, match="Unsupported file type"):
            detect_file_type(None, "https://example.com/file.docx")


class TestExtractText:
    """T1.2 / T2.4 - PDF text extraction."""

    def test_extracts_text_from_valid_pdf(self, sample_pdf_path: str) -> None:
        text = extract_text(sample_pdf_path)
        assert "test paper" in text.lower()
        assert len(text) > 0

    def test_raises_on_encrypted_pdf(self, encrypted_pdf_path: str) -> None:
        with pytest.raises(ValueError, match="encrypted"):
            extract_text(encrypted_pdf_path)

    def test_raises_on_empty_pdf(self, empty_pdf_path: str) -> None:
        with pytest.raises(ValueError, match="No extractable text"):
            extract_text(empty_pdf_path)

    def test_raises_on_corrupted_file(self, tmp_path) -> None:
        bad = tmp_path / "bad.pdf"
        bad.write_bytes(b"this is not a PDF file at all")
        with pytest.raises(ValueError, match="Cannot open PDF"):
            extract_text(bad)
