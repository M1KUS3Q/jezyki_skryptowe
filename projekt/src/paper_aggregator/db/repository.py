"""Database layer - SQLite repository using the Repository pattern.

Schema follows REQUIREMENTS.md §4:
- papers, authors, paper_authors, tags, paper_tags
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS papers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT UNIQUE NOT NULL,
    title TEXT,
    year INTEGER,
    primary_field TEXT,
    sub_field TEXT,
    abstract_summary TEXT,
    content_hash TEXT,
    file_path TEXT NOT NULL,
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS authors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS paper_authors (
    paper_id INTEGER NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    author_id INTEGER NOT NULL REFERENCES authors(id) ON DELETE CASCADE,
    PRIMARY KEY (paper_id, author_id)
);

CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    category TEXT NOT NULL CHECK (category IN ('keyword', 'methodology'))
);

CREATE TABLE IF NOT EXISTS paper_tags (
    paper_id INTEGER NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (paper_id, tag_id)
);

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
"""


class PaperRepository:
    """Repository for paper CRUD operations on the local SQLite database."""

    def __init__(self, db_path: Path | str) -> None:
        self.db_path = str(db_path)

    def _connect(self) -> sqlite3.Connection:
        """Create a new connection with WAL mode and foreign keys enabled."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def initialize(self) -> None:
        """Create the database schema if it does not exist."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(SCHEMA_SQL)

    # --- Placeholder methods to be implemented ---

    def add_paper(self, url: str, file_path: str, content_hash: str | None = None) -> int:
        """Insert a new paper record and return its ID."""
        ...

    def paper_exists(self, url: str) -> bool:
        """Check whether a paper with the given URL already exists."""
        ...

    def search_papers(
        self,
        tags: list[str] | None = None,
        author: str | None = None,
        field: str | None = None,
        year: str | None = None,
        limit: int = 50,
    ) -> list[dict]:
        """Search papers with the given filters."""
        ...

    def get_paper(self, paper_id: int) -> dict | None:
        """Get full details for a single paper."""
        ...

    def remove_paper(self, paper_id: int) -> bool:
        """Delete a paper and its join-table rows. Returns True if deleted."""
        ...

    def list_all(self, tag: str | None = None, limit: int = 50) -> list[dict]:
        """List papers, newest first, optionally filtered by tag."""
        ...

    def list_tags(self) -> list[dict]:
        """Return all distinct tags with paper counts."""
        ...
