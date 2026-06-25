"""BibTeX reference generation.

Produces ``.bib`` entries from paper records stored in the database.
No dependencies on CLI or network - pure string formatting.
"""

from __future__ import annotations

import re
import unicodedata

# Words to skip when building the citation key from the title.
_STOPWORDS: frozenset[str] = frozenset({
    "a", "an", "the", "on", "in", "of", "for", "to", "at", "by",
    "and", "or", "with", "from", "into", "onto", "upon",
})


def _to_ascii(s: str) -> str:
    """Normalise *s* to ASCII by stripping diacritics (NFKD)."""
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()


def _first_title_word(title: str) -> str:
    """Return the first non-stopword word from *title*, lowercased.

    Falls back to the first word (stopword or not) if every word is a
    stopword or the title is empty.
    """
    # Normalise to ASCII first so accented letters (Ü, é, etc.) are
    # decomposed before we split on word boundaries.
    clean = _to_ascii(title)
    # Drop punctuation so "Attention: Is" -> ["Attention", "Is"]
    words = re.findall(r"[A-Za-z0-9]+", clean)
    if not words:
        return "untitled"

    for w in words:
        if w.lower() not in _STOPWORDS:
            return w.lower()
    # All words are stopwords - use the first one anyway.
    return words[0].lower()


def _last_name(author: str) -> str:
    """Extract the last-name portion of a ``"LastName, FirstName"`` string."""
    return author.split(",")[0].strip()


def generate_citation_key(
    authors_str: str,
    year: int | None,
    title: str,
) -> str:
    """Build a BibTeX citation key.

    Format: ``FirstAuthorLastNameYEARFirstTitleWord``, all lowercase ASCII.

    Parameters
    ----------
    authors_str:
        Comma-separated list of ``"LastName, FirstName"`` authors.
    year:
        Publication year (uses ``"XXXX"`` when ``None``).
    title:
        Paper title.

    Returns
    -------
    str
        e.g. ``"vaswani2017attention"``

    Examples
    --------
    >>> generate_citation_key("Vaswani, Ashish, Shazeer, Noam", 2017,
    ...     "Attention Is All You Need")
    'vaswani2017attention'
    """
    first_author = authors_str.split(",")[0].strip()
    last = _to_ascii(_last_name(first_author)).lower()
    last = re.sub(r"[^a-z0-9]", "", last)

    year_str = str(year) if year else "XXXX"
    word = _to_ascii(_first_title_word(title)).lower()
    word = re.sub(r"[^a-z0-9]", "", word)

    return f"{last}{year_str}{word}"


def format_bibtex(paper: dict, *, entry_type: str = "article") -> str:
    """Format a single paper dict as a BibTeX entry.

    Parameters
    ----------
    paper:
        A dict from :meth:`PaperRepository.get_paper` (or equivalent).
        Expected keys: ``title``, ``authors``, ``year``, ``url``,
        ``abstract_summary``.
    entry_type:
        BibTeX entry type - usually ``"article"`` or ``"inproceedings"``.

    Returns
    -------
    str
        A ready-to-paste ``.bib`` entry.
    """
    key = generate_citation_key(
        paper.get("authors", ""),
        paper.get("year"),
        paper.get("title", ""),
    )

    # BibTeX requires "and" between full "LastName, FirstName" names.
    # The DB stores authors as a flat comma-separated string:
    # "LastName1, FirstName1, LastName2, FirstName2".
    authors = paper.get("authors", "")
    parts = [a.strip() for a in authors.split(",") if a.strip()]
    # Group every two parts back into a "LastName, FirstName" pair.
    author_names: list[str] = []
    i = 0
    while i < len(parts):
        if i + 1 < len(parts):
            author_names.append(f"{parts[i]}, {parts[i + 1]}")
            i += 2
        else:
            # Odd number of parts - treat as single name.
            author_names.append(parts[i])
            i += 1
    bibtex_authors = " and ".join(author_names)

    lines: list[str] = []
    lines.append(f"@{entry_type}{{{key},")
    lines.append(f"  author = {{{bibtex_authors}}},")
    lines.append(f"  title = {{{paper.get('title', '')}}},")

    year = paper.get("year")
    if year:
        lines.append(f"  year = {{{year}}},")

    url = paper.get("url", "")
    if url:
        lines.append(f"  url = {{{url}}},")

    abstract = paper.get("abstract_summary", "")
    if abstract:
        # Truncate long abstracts so the note doesn't bloat.
        if len(abstract) > 300:
            abstract = abstract[:297] + "..."
        lines.append(f"  note = {{{abstract}}},")

    lines.append("}")

    return "\n".join(lines)
