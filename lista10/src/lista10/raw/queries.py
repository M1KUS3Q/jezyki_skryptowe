"""Raw SQL queries for Task 3 - stop timetable statistics.

All functions take a ``sqlite3.Connection`` and return simple Python values.
"""

from __future__ import annotations

import sqlite3
from typing import Any


# ---------------------------------------------------------------------------
# Stop listing
# ---------------------------------------------------------------------------

def get_all_stops(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Return every stop as ``{stop_id, stop_code, stop_name}``."""
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT stop_id, stop_code, stop_name FROM stops ORDER BY stop_name"
    ).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Task 3a - number of different lines serving a stop
# ---------------------------------------------------------------------------

def count_lines_at_stop(conn: sqlite3.Connection, stop_id: str) -> int:
    """Number of distinct route short-names that call at *stop_id*."""
    row = conn.execute(
        """
        SELECT COUNT(DISTINCT r.route_short_name) AS cnt
        FROM routes r
        JOIN trips t       ON r.route_id = t.route_id
        JOIN stop_times st ON t.trip_id = st.trip_id
        WHERE st.stop_id = ?
        """,
        (stop_id,),
    ).fetchone()
    return row[0]


# ---------------------------------------------------------------------------
# Task 3b - number of departures from a stop
# ---------------------------------------------------------------------------

def count_departures(conn: sqlite3.Connection, stop_id: str) -> int:
    """Total number of departures from *stop_id*."""
    row = conn.execute(
        "SELECT COUNT(*) FROM stop_times WHERE stop_id = ?",
        (stop_id,),
    ).fetchone()
    return row[0]


# ---------------------------------------------------------------------------
# Task 3c - earliest / latest departure
# ---------------------------------------------------------------------------

def earliest_departure(conn: sqlite3.Connection, stop_id: str) -> str | None:
    """Earliest departure time (HH:MM:SS) from *stop_id*."""
    row = conn.execute(
        "SELECT MIN(departure_time) FROM stop_times WHERE stop_id = ?",
        (stop_id,),
    ).fetchone()
    return row[0]


def latest_departure(conn: sqlite3.Connection, stop_id: str) -> str | None:
    """Latest departure time (HH:MM:SS) from *stop_id*."""
    row = conn.execute(
        "SELECT MAX(departure_time) FROM stop_times WHERE stop_id = ?",
        (stop_id,),
    ).fetchone()
    return row[0]


# ---------------------------------------------------------------------------
# Task 3d - most common directions (headsigns)
# ---------------------------------------------------------------------------

def most_common_directions(
    conn: sqlite3.Connection, stop_id: str, limit: int = 5
) -> list[dict[str, Any]]:
    """Top *limit* headsigns by departure count at *stop_id*."""
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT t.trip_headsign, COUNT(*) AS cnt
        FROM trips t
        JOIN stop_times st ON t.trip_id = st.trip_id
        WHERE st.stop_id = ?
        GROUP BY t.trip_headsign
        ORDER BY cnt DESC
        LIMIT ?
        """,
        (stop_id, limit),
    ).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Task 3e - non-trivial custom query
# ---------------------------------------------------------------------------

def custom_query(
    conn: sqlite3.Connection, stop_id: str
) -> list[dict[str, Any]]:
    """Departures per hour of day at *stop_id*.

    Extracts the hour from ``departure_time`` (handling values ≥ 24 h),
    groups by hour, and returns the count of departures in each hour bucket.
    """
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT
            CAST(SUBSTR(departure_time, 1, INSTR(departure_time, ':') - 1) AS INTEGER) AS hour,
            COUNT(*) AS cnt
        FROM stop_times
        WHERE stop_id = ?
        GROUP BY hour
        ORDER BY hour
        """,
        (stop_id,),
    ).fetchall()
    return [dict(r) for r in rows]
