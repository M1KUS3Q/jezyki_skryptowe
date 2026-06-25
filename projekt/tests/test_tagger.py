"""Unit tests for LLM tagging - truncation, prompt building, and tag parsing."""

import json

import pytest

from paper_aggregator.domain.models import PaperTags
from paper_aggregator.domain.tagger import (
    build_tagging_prompt,
    tag_paper,
    truncate_text,
)


class TestTruncateText:
    """T1.10 - text truncation."""

    def test_no_truncation_when_under_limit(self) -> None:
        text, was_truncated = truncate_text("short text", 100)
        assert text == "short text"
        assert was_truncated is False

    def test_no_truncation_when_exactly_at_limit(self) -> None:
        text, was_truncated = truncate_text("12345", 5)
        assert text == "12345"
        assert was_truncated is False

    def test_truncation_when_over_limit(self) -> None:
        text, was_truncated = truncate_text("1234567890", 5)
        assert text == "12345"
        assert was_truncated is True

    def test_empty_string(self) -> None:
        text, was_truncated = truncate_text("", 10)
        assert text == ""
        assert was_truncated is False


class TestBuildTaggingPrompt:
    """Prompt construction."""

    def test_includes_paper_text(self) -> None:
        prompt = build_tagging_prompt("Hello world")
        assert "Hello world" in prompt
        assert "BEGIN PAPER TEXT" in prompt
        assert "END PAPER TEXT" in prompt


class TestTagPaper:
    """T1.3 / T1.4 - LLM response parsing and validation."""

    def test_parses_valid_response(
        self,
        mock_openai_client: object,
        sample_paper_tags: PaperTags,
    ) -> None:
        result = tag_paper("some paper text", client=mock_openai_client)
        assert result == sample_paper_tags

    def test_retries_on_validation_failure(
        self,
        sample_paper_tags: PaperTags,
    ) -> None:
        from unittest.mock import MagicMock

        call_count = [0]

        def fake_create(*, model, messages, response_format, temperature):  # noqa: ARG001
            call_count[0] += 1
            if call_count[0] == 1:
                return MagicMock(
                    choices=[MagicMock(message=MagicMock(content='{"bad": "json'))]
                )
            return MagicMock(
                choices=[
                    MagicMock(
                        message=MagicMock(content=sample_paper_tags.model_dump_json())
                    )
                ]
            )

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = fake_create

        result = tag_paper("text", client=mock_client)
        assert result.title == sample_paper_tags.title
        assert call_count[0] == 2

    def test_raises_when_all_retries_exhausted(self) -> None:
        from unittest.mock import MagicMock

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="definitely not json"))]
        )

        with pytest.raises(ValueError, match="Failed to parse LLM response"):
            tag_paper("text", client=mock_client, max_retries=0)

    def test_raises_when_no_api_key_and_no_client(self) -> None:
        # Ensure the settings singleton has no key for this test.
        from paper_aggregator.config.settings import settings

        old_key = settings.api_key
        settings.api_key = ""
        try:
            with pytest.raises(ValueError, match="No API key configured"):
                tag_paper("text")
        finally:
            settings.api_key = old_key

    def test_rejects_string_instead_of_list_for_authors(self) -> None:
        """T1.4 - authors as string instead of list -> rejected."""
        from unittest.mock import MagicMock

        mock_client = MagicMock()
        bad_response = json.dumps({
            "title": "Test",
            "authors": "Doe, John",  # should be a list
            "year": 2024,
            "primary_field": "CS",
            "sub_field": None,
            "keywords": ["test"],
            "methodology": ["testing"],
            "abstract_summary": "Summary.",
        })
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content=bad_response))]
        )

        with pytest.raises(ValueError, match="Failed to parse"):
            tag_paper("text", client=mock_client, max_retries=0)

    def test_rejects_missing_required_field(self) -> None:
        """T1.3 - missing required field -> rejected."""
        from unittest.mock import MagicMock

        mock_client = MagicMock()
        bad_response = json.dumps({
            "title": "Test",
            # missing 'authors'
            "primary_field": "CS",
            "keywords": ["test"],
            "methodology": ["testing"],
            "abstract_summary": "Summary.",
        })
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content=bad_response))]
        )

        with pytest.raises(ValueError, match="Failed to parse"):
            tag_paper("text", client=mock_client, max_retries=0)
