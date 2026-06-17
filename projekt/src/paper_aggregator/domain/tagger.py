"""LLM tagging - send extracted text to the LLM and parse the response."""

from __future__ import annotations

import json
from typing import Any

from openai import OpenAI

from paper_aggregator.config.settings import settings
from paper_aggregator.domain.models import PaperTags

# System prompt — the JSON schema is enforced by the API's structured-output
# mode, so the prompt only needs to describe the *semantics* of each field.
_SYSTEM_PROMPT = """\
You are a research librarian assistant. Given the text of an academic paper, \
extract structured metadata according to the supplied JSON schema. \
Be precise and concise.

Keyword guidelines:
- Include a mix of **broad** terms (useful for browsing: "AI", "education", \
"robotics", "climate") and **specific** terms (the exact technique or topic: \
"BERT", "reinforcement learning", "coral bleaching").
- Prefer commonly-used abbreviations where they are the standard in the field \
(e.g. "AI" alongside "artificial intelligence", "NLP" alongside "natural \
language processing", "CNN" for convolutional neural networks).
- Think like a search engine: what terms would a researcher type to find this \
paper? Include both the general category and the distinctive contribution.
- Use lowercase except for proper nouns and standard acronyms (AI, LSTM, BERT)."""


def _build_openai_schema(pydantic_schema: dict[str, Any]) -> dict[str, Any]:
    """Convert a Pydantic-generated JSON schema into one compatible with
    OpenAI's structured-outputs ``strict`` mode.

    Specifically:
    - Replaces ``anyOf`` (e.g. ``[{"type":"string"},{"type":"null"}]``) with
      the ``type: ["string", "null"]`` form.
    - Strips ``title`` and ``default`` noise from property definitions.
    - Ensures ``additionalProperties: false`` and that all properties
      appear in ``required``.
    """
    properties: dict[str, Any] = {}
    required: list[str] = []

    for name, prop in pydantic_schema.get("properties", {}).items():
        cleaned: dict[str, Any] = {}
        required.append(name)

        if "anyOf" in prop:
            types: list[str] = []
            for opt in prop["anyOf"]:
                if isinstance(opt, dict) and "type" in opt:
                    types.append(opt["type"])
                elif isinstance(opt, dict) and "const" in opt and opt["const"] is None:
                    types.append("null")
            cleaned["type"] = types
        elif "type" in prop:
            cleaned["type"] = prop["type"]

        if "minItems" in prop:
            cleaned["minItems"] = prop["minItems"]
        if "maxItems" in prop:
            cleaned["maxItems"] = prop["maxItems"]
        if "items" in prop:
            cleaned["items"] = prop["items"]

        properties[name] = cleaned

    return {
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
    }


# Pre-computed at import time.
_STRICT_SCHEMA = _build_openai_schema(PaperTags.model_json_schema())


def truncate_text(text: str, max_chars: int) -> tuple[str, bool]:
    """Truncate *text* to *max_chars* characters.

    Returns (truncated_text, was_truncated).
    """
    if len(text) <= max_chars:
        return text, False
    return text[:max_chars], True


def build_tagging_prompt(text: str) -> str:
    """Build the user prompt that instructs the LLM to tag a paper.

    Returns the full prompt string wrapping the paper text with
    instructions for structured metadata extraction.
    """
    return (
        "Analyze the following academic paper text and extract structured "
        "metadata as JSON:\n\n"
        "--- BEGIN PAPER TEXT ---\n"
        f"{text}\n"
        "--- END PAPER TEXT ---\n"
    )


def tag_paper(
    text: str,
    model: str | None = None,
    *,
    client: OpenAI | None = None,
    max_retries: int = 1,
) -> PaperTags:
    """Send paper text to the LLM and return validated tags.

    Uses OpenAI's structured-outputs mode (``json_schema`` with
    ``strict: true``) so the model is constrained to return valid JSON
    matching the :class:`PaperTags` schema.

    Parameters
    ----------
    text:
        The (possibly truncated) paper text to analyze.
    model:
        Optional model override.  Uses :attr:`settings.model` when ``None``.
    client:
        Optional pre-configured :class:`OpenAI` client.  Created from
        :mod:`~paper_aggregator.config.settings` when ``None``, enabling
        dependency injection for tests.
    max_retries:
        How many additional attempts on Pydantic validation failure
        (default 1, so 2 total).

    Returns
    -------
    PaperTags
        Validated structured tags.

    Raises
    ------
    ValueError
        If the LLM response cannot be parsed after all retries, or if no
        API key is configured.
    """
    if client is None:
        if not settings.api_key:
            raise ValueError(
                "No API key configured. Set the PAPER_AGGREGATOR_API_KEY "
                "environment variable."
            )
        client = OpenAI(
            base_url=settings.api_base_url,
            api_key=settings.api_key,
        )

    resolved_model = model or settings.model
    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": build_tagging_prompt(text)},
    ]

    last_error: Exception | None = None
    last_raw: str = ""

    for attempt in range(max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=resolved_model,
                messages=messages,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "paper_tags",
                        "schema": _STRICT_SCHEMA,
                        "strict": True,
                    },
                },
                temperature=0.1,
            )
            content: str | None = response.choices[0].message.content
            if content is None:
                raise ValueError("LLM returned an empty response.")

            last_raw = content
            return PaperTags.model_validate_json(content)

        except (json.JSONDecodeError, ValueError) as exc:
            last_error = exc
            if attempt < max_retries:
                messages.append(
                    {"role": "assistant", "content": last_raw},
                )
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            "Your previous response was not valid JSON "
                            "or did not match the required schema. "
                            f"Error: {exc}. "
                            "Please return ONLY a valid JSON object "
                            "matching the schema."
                        ),
                    }
                )

    raise ValueError(
        f"Failed to parse LLM response after {max_retries + 1} attempts. "
        f"Last error: {last_error}"
    )
