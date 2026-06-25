"""Integration tests that exercise the real OpenAI API.

These tests require a valid ``PAPER_AGGREGATOR_API_KEY`` (loaded from
``.env`` automatically by the settings module).  They are skipped when
no key is available.

Run with::

    pytest tests/test_integration.py -v
"""

import pytest

from paper_aggregator.config.settings import settings


pytestmark = pytest.mark.skipif(
    not settings.api_key,
    reason="PAPER_AGGREGATOR_API_KEY not set - set it in .env to run integration tests",
)


# A realistic excerpt from a well-known paper abstract.
ATTENTION_PAPER = """
Title: Attention Is All You Need

Authors: Vaswani, Ashish; Shazeer, Noam; Parmar, Niki; Uszkoreit, Jakob;
Jones, Llion; Gomez, Aidan N.; Kaiser, Lukasz; Polosukhin, Illia

Abstract: The dominant sequence transduction models are based on complex
recurrent or convolutional neural networks that include an encoder and a
decoder. The best performing models also connect the encoder and decoder
through an attention mechanism. We propose a new simple network architecture,
the Transformer, based solely on attention mechanisms, dispensing with
recurrence and convolutions entirely. Experiments on two machine translation
tasks show that these models are superior in quality while being more
parallelizable and requiring significantly less time to train.
"""


class TestRealTagging:
    """T2.1 - end-to-end tagging with a real LLM."""

    def test_tags_well_known_paper(self) -> None:
        from paper_aggregator.domain.tagger import tag_paper

        result = tag_paper(ATTENTION_PAPER)

        # Basic shape checks
        assert isinstance(result.title, str)
        assert len(result.title) > 0
        assert isinstance(result.authors, list)
        assert len(result.authors) >= 1
        assert all(isinstance(a, str) for a in result.authors)
        assert isinstance(result.year, int) or result.year is None
        assert isinstance(result.primary_field, str)
        assert len(result.primary_field) > 0
        assert isinstance(result.keywords, list)
        assert 1 <= len(result.keywords) <= 8
        assert isinstance(result.methodology, list)
        assert len(result.methodology) >= 1
        assert isinstance(result.abstract_summary, str)
        assert len(result.abstract_summary) > 20

        # Semantic checks - the LLM should produce a reasonable title.
        title_lower = result.title.lower()
        assert "attention" in title_lower or "transformer" in title_lower

        # Keywords should be non-empty and sensible.
        assert all(len(k) > 1 for k in result.keywords)


class TestEndToEndPipeline:
    """T2.1 - complete ingestion pipeline with real LLM, local DB."""

    def test_full_add_flow(self, tmp_path, db_repo) -> None:  # noqa: ARG002
        import fitz
        from paper_aggregator.domain.ingestor import compute_content_hash, extract_text
        from paper_aggregator.domain.tagger import tag_paper, truncate_text

        # Create a small test PDF on disk.
        pdf_path = tmp_path / "test.pdf"
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text(
            (72, 72),
            "Deep Learning for Natural Language Processing\n\n"
            "Authors: John Smith, Alice Brown\n\n"
            "Abstract: We present a novel deep learning framework for NLP tasks. "
            "Our model uses transformer architectures with self-attention "
            "mechanisms to achieve state-of-the-art results on sentiment "
            "analysis and named entity recognition benchmarks. "
            "Experiments on the GLUE benchmark show a 5% improvement over "
            "previous methods.\n\n"
            "Keywords: natural language processing, deep learning, transformers, "
            "sentiment analysis, named entity recognition.\n\n"
            "1. Introduction\n"
            "Natural language processing has seen rapid advances...",
        )
        doc.save(str(pdf_path))
        doc.close()

        # Extract text.
        text = extract_text(pdf_path)
        assert len(text) > 50

        # Truncate and tag.
        truncated, was_truncated = truncate_text(text, settings.max_context_chars)
        assert len(truncated) <= settings.max_context_chars

        tags = tag_paper(truncated)

        # Store in DB.
        content_hash = compute_content_hash(pdf_path)
        paper_id = db_repo.add_paper(
            "https://example.com/nlp-paper.pdf",
            str(pdf_path),
            content_hash,
        )
        db_repo.save_paper_metadata(
            paper_id=paper_id,
            title=tags.title,
            authors=tags.authors,
            year=tags.year,
            primary_field=tags.primary_field,
            sub_field=tags.sub_field,
            keywords=tags.keywords,
            methodology=tags.methodology,
            abstract_summary=tags.abstract_summary,
        )

        # Verify it's retrievable.
        paper = db_repo.get_paper(paper_id)
        assert paper is not None
        assert paper["title"] == tags.title
        assert paper["year"] == tags.year

        # Verify it appears in search.
        results = db_repo.search_papers(author="Smith")
        assert len(results) >= 1
