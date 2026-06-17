"""ORM (SQLAlchemy) CRUD operations - create database and load GTFS data.

Thin wrappers around ``lista10.models`` and ``lista10.database`` so the CLI
scripts can treat raw and ORM paths identically.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from lista10.database import create_database as _engine_create
from lista10.database import create_engine_for, create_session_factory
from lista10.models import Calendar, Route, Stop, StopTime, Trip


# ---------------------------------------------------------------------------
# Schema creation
# ---------------------------------------------------------------------------

def create_database(path: str | Path) -> None:
    """Create a fresh database at *path* using ORM model metadata.

    Delegates to ``lista10.database.create_database``, which removes any
    existing file, creates the engine, and calls ``Base.metadata.create_all``.
    """
    engine = _engine_create(path)
    engine.dispose()


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_all(db_path: str | Path, data: dict[str, list[dict[str, Any]]]) -> None:
    """Insert all GTFS data into the database using ORM model instances.

    *data* is the dict returned by ``lista10.gtfs.reader.read_gtfs()``.
    Each row is converted to a model instance and flushed in FK-safe order.
    """
    engine = create_engine_for(db_path)
    SessionFactory = create_session_factory(engine)

    with SessionFactory() as session:
        # FK-safe order: parents first, then children
        _load_stops(session, data.get("stops", []))
        _load_routes(session, data.get("routes", []))
        _load_calendar(session, data.get("calendar", []))
        session.flush()  # make PKs visible to FK relationships

        _load_trips(session, data.get("trips", []))
        session.flush()

        _load_stop_times(session, data.get("stop_times", []))
        session.commit()

    engine.dispose()


# ---------------------------------------------------------------------------
# Per-table loaders
# ---------------------------------------------------------------------------

def _load_stops(session: Session, rows: list[dict[str, Any]]) -> None:
    instances = [
        Stop(
            stop_id=r["stop_id"],
            stop_code=r["stop_code"],
            stop_name=r["stop_name"],
            stop_lat=float(r["stop_lat"]),
            stop_lon=float(r["stop_lon"]),
        )
        for r in rows
    ]
    session.add_all(instances)


def _load_routes(session: Session, rows: list[dict[str, Any]]) -> None:
    instances = [
        Route(
            route_id=r["route_id"],
            agency_id=r["agency_id"],
            route_short_name=r["route_short_name"],
            route_long_name=r["route_long_name"],
            route_desc=r.get("route_desc") or None,
            route_type=int(r["route_type"]),
        )
        for r in rows
    ]
    session.add_all(instances)


def _load_calendar(session: Session, rows: list[dict[str, Any]]) -> None:
    instances = [
        Calendar(
            service_id=r["service_id"],
            monday=int(r["monday"]),
            tuesday=int(r["tuesday"]),
            wednesday=int(r["wednesday"]),
            thursday=int(r["thursday"]),
            friday=int(r["friday"]),
            saturday=int(r["saturday"]),
            sunday=int(r["sunday"]),
            start_date=r["start_date"],
            end_date=r["end_date"],
        )
        for r in rows
    ]
    session.add_all(instances)


def _load_trips(session: Session, rows: list[dict[str, Any]]) -> None:
    instances = [
        Trip(
            trip_id=r["trip_id"],
            route_id=r["route_id"],
            service_id=r["service_id"],
            trip_headsign=r.get("trip_headsign") or None,
            direction_id=int(r["direction_id"]) if r.get("direction_id") else None,
        )
        for r in rows
    ]
    session.add_all(instances)


def _load_stop_times(session: Session, rows: list[dict[str, Any]]) -> None:
    instances = [
        StopTime(
            trip_id=r["trip_id"],
            arrival_time=r["arrival_time"],
            departure_time=r["departure_time"],
            stop_id=r["stop_id"],
            stop_sequence=int(r["stop_sequence"]),
        )
        for r in rows
    ]
    session.add_all(instances)
