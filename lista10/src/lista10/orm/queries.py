"""ORM (SQLAlchemy) queries for Task 3 - stop timetable statistics.

All functions take a ``sqlalchemy.orm.Session`` and return simple Python
values.  The function signatures mirror ``lista10.raw.queries`` so the CLI
can swap between the two.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from lista10.models import Route, Stop, StopTime, Trip


# ---------------------------------------------------------------------------
# Stop listing
# ---------------------------------------------------------------------------

def get_all_stops(session: Session) -> list[dict[str, Any]]:
    """Return every stop as ``{stop_id, stop_code, stop_name}``."""
    stops = session.query(Stop).order_by(Stop.stop_name).all()
    return [
        {"stop_id": s.stop_id, "stop_code": s.stop_code, "stop_name": s.stop_name}
        for s in stops
    ]


# ---------------------------------------------------------------------------
# Task 3a - number of different lines serving a stop
# ---------------------------------------------------------------------------

def count_lines_at_stop(session: Session, stop_id: str) -> int:
    """Number of distinct route short-names that call at *stop_id*."""
    return (
        session.query(Route.route_short_name)
        .join(Trip, Route.route_id == Trip.route_id)
        .join(StopTime, Trip.trip_id == StopTime.trip_id)
        .filter(StopTime.stop_id == stop_id)
        .distinct()
        .count()
    )


# ---------------------------------------------------------------------------
# Task 3b - number of departures from a stop
# ---------------------------------------------------------------------------

def count_departures(session: Session, stop_id: str) -> int:
    """Total number of departures from *stop_id*."""
    return (
        session.query(StopTime)
        .filter(StopTime.stop_id == stop_id)
        .count()
    )


# ---------------------------------------------------------------------------
# Task 3c - earliest / latest departure
# ---------------------------------------------------------------------------

def earliest_departure(session: Session, stop_id: str) -> str | None:
    """Earliest departure time (HH:MM:SS) from *stop_id*."""
    return (
        session.query(func.min(StopTime.departure_time))
        .filter(StopTime.stop_id == stop_id)
        .scalar()
    )


def latest_departure(session: Session, stop_id: str) -> str | None:
    """Latest departure time (HH:MM:SS) from *stop_id*."""
    return (
        session.query(func.max(StopTime.departure_time))
        .filter(StopTime.stop_id == stop_id)
        .scalar()
    )


# ---------------------------------------------------------------------------
# Task 3d - most common directions (headsigns)
# ---------------------------------------------------------------------------

def most_common_directions(
    session: Session, stop_id: str, limit: int = 5
) -> list[dict[str, Any]]:
    """Top *limit* headsigns by departure count at *stop_id*."""
    rows = (
        session.query(
            Trip.trip_headsign,
            func.count().label("cnt"),
        )
        .join(StopTime, Trip.trip_id == StopTime.trip_id)
        .filter(StopTime.stop_id == stop_id)
        .group_by(Trip.trip_headsign)
        .order_by(func.count().desc())
        .limit(limit)
        .all()
    )
    return [{"trip_headsign": r[0], "cnt": r[1]} for r in rows]


# ---------------------------------------------------------------------------
# Task 3e - non-trivial custom query (ORM aggregate)
# ---------------------------------------------------------------------------

def custom_query(
    session: Session, stop_id: str
) -> list[dict[str, Any]]:
    """Top 5 lines (route_short_name) by departure count at *stop_id*.

    Joins through stop_times -> trips -> routes, groups by line number,
    and returns the most-frequent lines serving this stop.
    """
    rows = (
        session.query(
            Route.route_short_name,
            func.count().label("cnt"),
        )
        .select_from(StopTime)
        .join(Trip, StopTime.trip_id == Trip.trip_id)
        .join(Route, Trip.route_id == Route.route_id)
        .filter(StopTime.stop_id == stop_id)
        .group_by(Route.route_short_name)
        .order_by(func.count().desc())
        .limit(5)
        .all()
    )
    return [{"route_short_name": r[0], "cnt": r[1]} for r in rows]
