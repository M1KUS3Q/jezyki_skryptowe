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

    # --- Public API ---

    def add_paper(
        self,
        url: str,
        file_path: str,
        content_hash: str | None = None,
    ) -> int:
        """Insert a new paper record and return its ID.

        Raises :class:`sqlite3.IntegrityError` if the URL already exists.
        """
        with self._connect() as conn:
            cursor = conn.execute(
                "INSERT INTO papers (url, file_path, content_hash) VALUES (?, ?, ?)",
                (url, file_path, content_hash),
            )
            return cursor.lastrowid  # type: ignore[return-value]

    def save_paper_metadata(
        self,
        paper_id: int,
        title: str,
        authors: list[str],
        year: int | None,
        primary_field: str,
        sub_field: str | None,
        keywords: list[str],
        methodology: list[str],
        abstract_summary: str,
    ) -> None:
        """Store full paper metadata, linking authors and tags.

        Call this after :meth:`add_paper` once the LLM returns tags.
        """
        with self._connect() as conn:
            conn.execute(
                """UPDATE papers
                   SET title = ?, year = ?, primary_field = ?, sub_field = ?,
                       abstract_summary = ?
                   WHERE id = ?""",
                (title, year, primary_field, sub_field, abstract_summary, paper_id),
            )

            # Link authors.
            for author_name in authors:
                author_id = self._get_or_create_author(conn, author_name)
                conn.execute(
                    "INSERT OR IGNORE INTO paper_authors (paper_id, author_id) "
                    "VALUES (?, ?)",
                    (paper_id, author_id),
                )

            # Link keyword tags.
            for kw in keywords:
                tag_id = self._get_or_create_tag(conn, kw, "keyword")
                conn.execute(
                    "INSERT OR IGNORE INTO paper_tags (paper_id, tag_id) "
                    "VALUES (?, ?)",
                    (paper_id, tag_id),
                )

            # Link methodology tags.
            for meth in methodology:
                tag_id = self._get_or_create_tag(conn, meth, "methodology")
                conn.execute(
                    "INSERT OR IGNORE INTO paper_tags (paper_id, tag_id) "
                    "VALUES (?, ?)",
                    (paper_id, tag_id),
                )

    def paper_exists(self, url: str) -> bool:
        """Check whether a paper with the given URL already exists."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM papers WHERE url = ?", (url,)
            ).fetchone()
            return row is not None

    def search_papers(
        self,
        tags: list[str] | None = None,
        author: str | None = None,
        field: str | None = None,
        year: str | None = None,
        limit: int = 50,
    ) -> list[dict]:
        """Search papers with the given filters.

        Returns a list of dicts with keys: ``id``, ``title``, ``year``,
        ``primary_field``, ``sub_field``, ``abstract_summary``,
        ``authors`` (comma-separated), ``keywords`` (comma-separated),
        ``methodology`` (comma-separated).
        """
        conditions: list[str] = []
        params: list[str | int] = []

        if tags:
            # AND semantics: paper must match ALL specified tags.
            placeholders = ",".join("?" for _ in tags)
            conditions.append(
                f"""p.id IN (
                    SELECT pt.paper_id FROM paper_tags pt
                    JOIN tags t ON t.id = pt.tag_id
                    WHERE t.name IN ({placeholders})
                    GROUP BY pt.paper_id
                    HAVING COUNT(DISTINCT t.name) = ?
                )"""
            )
            params.extend(tags)
            params.append(len(tags))

        if author:
            conditions.append(
                "p.id IN ("
                "  SELECT pa.paper_id FROM paper_authors pa"
                "  JOIN authors a ON a.id = pa.author_id"
                "  WHERE a.name LIKE ?"
                ")"
            )
            params.append(f"%{author}%")

        if field:
            conditions.append("(p.primary_field LIKE ? OR p.sub_field LIKE ?)")
            params.extend((f"%{field}%", f"%{field}%"))

        if year:
            from paper_aggregator.domain.search import parse_year_filter  # noqa: PLC0415
            y_from, y_to = parse_year_filter(year)
            if y_from is not None and y_to is not None:
                if y_from == y_to:
                    conditions.append("p.year = ?")
                    params.append(y_from)
                else:
                    conditions.append("p.year >= ? AND p.year <= ?")
                    params.extend((y_from, y_to))

        where = ""
        if conditions:
            where = "WHERE " + " AND ".join(conditions)

        query = f"""
            SELECT p.id, p.title, p.year, p.primary_field, p.sub_field,
                   p.abstract_summary,
                   GROUP_CONCAT(DISTINCT a.name) AS authors,
                   GROUP_CONCAT(DISTINCT CASE WHEN t.category = 'keyword' THEN t.name END) AS keywords,
                   GROUP_CONCAT(DISTINCT CASE WHEN t.category = 'methodology' THEN t.name END) AS methodology
            FROM papers p
            LEFT JOIN paper_authors pa ON pa.paper_id = p.id
            LEFT JOIN authors a ON a.id = pa.author_id
            LEFT JOIN paper_tags pt ON pt.paper_id = p.id
            LEFT JOIN tags t ON t.id = pt.tag_id
            {where}
            GROUP BY p.id
            ORDER BY p.ingested_at DESC, p.id DESC
            LIMIT ?
        """
        params.append(limit)

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]

    def get_paper(self, paper_id: int) -> dict | None:
        """Get full details for a single paper, including authors and tags."""
        with self._connect() as conn:
            row = conn.execute(
                """SELECT p.*,
                          GROUP_CONCAT(DISTINCT a.name) AS authors,
                          GROUP_CONCAT(DISTINCT CASE WHEN t.category = 'keyword' THEN t.name END) AS keywords,
                          GROUP_CONCAT(DISTINCT CASE WHEN t.category = 'methodology' THEN t.name END) AS methodology
                   FROM papers p
                   LEFT JOIN paper_authors pa ON pa.paper_id = p.id
                   LEFT JOIN authors a ON a.id = pa.author_id
                   LEFT JOIN paper_tags pt ON pt.paper_id = p.id
                   LEFT JOIN tags t ON t.id = pt.tag_id
                   WHERE p.id = ?
                   GROUP BY p.id""",
                (paper_id,),
            ).fetchone()
            return dict(row) if row else None

    def get_paper_by_url(self, url: str) -> dict | None:
        """Get a paper by its URL."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id FROM papers WHERE url = ?", (url,)
            ).fetchone()
            if row is None:
                return None
            return self.get_paper(row["id"])

    def remove_paper(self, paper_id: int) -> bool:
        """Delete a paper and its join-table rows. Returns True if deleted."""
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM papers WHERE id = ?", (paper_id,))
            return cursor.rowcount > 0

    def remove_paper_by_url(self, url: str) -> bool:
        """Delete a paper by URL. Returns True if deleted."""
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM papers WHERE url = ?", (url,))
            return cursor.rowcount > 0

    def list_all(
        self, tag: str | None = None, limit: int = 50
    ) -> list[dict]:
        """List papers, newest first, optionally filtered by tag."""
        if tag:
            query = """
                SELECT p.id, p.title, p.year, p.primary_field, p.sub_field,
                       p.abstract_summary,
                       GROUP_CONCAT(DISTINCT a.name) AS authors,
                       GROUP_CONCAT(DISTINCT CASE WHEN t.category = 'keyword' THEN t.name END) AS keywords
                FROM papers p
                LEFT JOIN paper_authors pa ON pa.paper_id = p.id
                LEFT JOIN authors a ON a.id = pa.author_id
                LEFT JOIN paper_tags pt ON pt.paper_id = p.id
                LEFT JOIN tags t ON t.id = pt.tag_id
                WHERE p.id IN (
                    SELECT pt2.paper_id FROM paper_tags pt2
                    JOIN tags t2 ON t2.id = pt2.tag_id
                    WHERE t2.name = ?
                )
                GROUP BY p.id
                ORDER BY p.ingested_at DESC, p.id DESC
                LIMIT ?
            """
            params: tuple = (tag, limit)
        else:
            query = """
                SELECT p.id, p.title, p.year, p.primary_field, p.sub_field,
                       p.abstract_summary,
                       GROUP_CONCAT(DISTINCT a.name) AS authors,
                       GROUP_CONCAT(DISTINCT CASE WHEN t.category = 'keyword' THEN t.name END) AS keywords
                FROM papers p
                LEFT JOIN paper_authors pa ON pa.paper_id = p.id
                LEFT JOIN authors a ON a.id = pa.author_id
                LEFT JOIN paper_tags pt ON pt.paper_id = p.id
                LEFT JOIN tags t ON t.id = pt.tag_id
                GROUP BY p.id
                ORDER BY p.ingested_at DESC, p.id DESC
                LIMIT ?
            """
            params = (limit,)

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]

    def list_tags(self) -> list[dict]:
        """Return all distinct tags with paper counts."""
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT t.name, t.category, COUNT(pt.paper_id) AS paper_count
                   FROM tags t
                   LEFT JOIN paper_tags pt ON pt.tag_id = t.id
                   GROUP BY t.id
                   ORDER BY paper_count DESC, t.name ASC"""
            ).fetchall()
            return [dict(row) for row in rows]

    # --- Internal helpers ---

    @staticmethod
    def _get_or_create_author(conn: sqlite3.Connection, name: str) -> int:
        """Return the ID of an author, inserting if necessary."""
        row = conn.execute(
            "SELECT id FROM authors WHERE name = ?", (name,)
        ).fetchone()
        if row:
            return row["id"]
        return conn.execute(
            "INSERT INTO authors (name) VALUES (?)", (name,)
        ).lastrowid

    @staticmethod
    def _get_or_create_tag(
        conn: sqlite3.Connection, name: str, category: str
    ) -> int:
        """Return the ID of a tag, inserting if necessary."""
        row = conn.execute(
            "SELECT id FROM tags WHERE name = ? AND category = ?",
            (name, category),
        ).fetchone()
        if row:
            return row["id"]
        return conn.execute(
            "INSERT INTO tags (name, category) VALUES (?, ?)",
            (name, category),
        ).lastrowid
