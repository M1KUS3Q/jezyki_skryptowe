"""Raw SQLite CRUD operations - create database and load GTFS data.

Uses only the standard-library ``sqlite3`` module.  The DDL lives in the
adjacent ``schema.sql`` file.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Schema creation
# ---------------------------------------------------------------------------

def create_database(path: str | Path) -> sqlite3.Connection:
    """Create a fresh SQLite database at *path* and return the connection.

    Any existing file at *path* is removed first.  WAL mode and foreign-key
    enforcement are enabled via PRAGMAs.
    """
    db_path = Path(path).resolve()
    db_path.unlink(missing_ok=True)

    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    _execute_schema(conn)
    conn.commit()
    return conn


def _execute_schema(conn: sqlite3.Connection) -> None:
    """Read and execute from ``schema.sql``."""
    schema_path = Path(__file__).resolve().parent / "schema.sql"
    conn.executescript(schema_path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_all(conn: sqlite3.Connection, data: dict[str, list[dict[str, Any]]]) -> None:
    """Insert all GTFS data from *data* into the database.

    *data* is the dict returned by ``lista10.gtfs.reader.read_gtfs()``.
    Tables are loaded in FK-safe order: stops, routes, calendar -> trips -> stop_times.
    """
    loaders = [
        ("stops",       _rows_for_stops),
        ("routes",      _rows_for_routes),
        ("calendar",    _rows_for_calendar),
        ("trips",       _rows_for_trips),
        ("stop_times",  _rows_for_stop_times),
    ]

    for table, transform in loaders:
        if table not in data:
            continue
        rows = [transform(r) for r in data[table]]
        _insert(conn, table, rows)


# ---------------------------------------------------------------------------
# Row transforms - extract + coerce the columns each table expects
# ---------------------------------------------------------------------------

def _rows_for_stops(r: dict[str, str]) -> tuple[str, str, str, float, float]:
    return (r["stop_id"], r["stop_code"], r["stop_name"],
            float(r["stop_lat"]), float(r["stop_lon"]))

def _rows_for_routes(r: dict[str, str]) -> tuple[str, str, str, str, str | None, int]:
    return (r["route_id"], r["agency_id"], r["route_short_name"],
            r["route_long_name"], r.get("route_desc") or None,
            int(r["route_type"]))

def _rows_for_calendar(r: dict[str, str]) -> tuple[str, int, int, int, int, int, int, int, str, str]:
    return (r["service_id"],
            int(r["monday"]), int(r["tuesday"]), int(r["wednesday"]),
            int(r["thursday"]), int(r["friday"]), int(r["saturday"]),
            int(r["sunday"]), r["start_date"], r["end_date"])

def _rows_for_trips(r: dict[str, str]) -> tuple[str, str, str, str | None, int | None]:
    return (r["trip_id"], r["route_id"], r["service_id"],
            r.get("trip_headsign") or None,
            int(r["direction_id"]) if r.get("direction_id") else None)

def _rows_for_stop_times(r: dict[str, str]) -> tuple[str, str, str, str, int]:
    return (r["trip_id"], r["arrival_time"], r["departure_time"],
            r["stop_id"], int(r["stop_sequence"]))


# ---------------------------------------------------------------------------
# Bulk insert helper
# ---------------------------------------------------------------------------

def _insert(conn: sqlite3.Connection, table: str, rows: list[tuple]) -> None:
    """Insert *rows* into *table* using ``executemany``."""
    if not rows:
        return

    columns = _column_names(table, rows[0])
    placeholders = ", ".join(["?"] * len(rows[0]))
    sql = f"INSERT OR REPLACE INTO {table} ({columns}) VALUES ({placeholders})"

    conn.executemany(sql, rows)
    conn.commit()


def _column_names(table: str, sample: tuple) -> str:
    """Return a comma-separated column list for *table*."""
    cols = {
        "stops":        "stop_id, stop_code, stop_name, stop_lat, stop_lon",
        "routes":       "route_id, agency_id, route_short_name, route_long_name, route_desc, route_type",
        "calendar":     "service_id, monday, tuesday, wednesday, thursday, friday, saturday, sunday, start_date, end_date",
        "trips":        "trip_id, route_id, service_id, trip_headsign, direction_id",
        "stop_times":   "trip_id, arrival_time, departure_time, stop_id, stop_sequence",
    }
    return cols[table]
