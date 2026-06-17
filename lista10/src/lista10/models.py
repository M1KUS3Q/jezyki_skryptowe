"""SQLAlchemy ORM models for the GTFS database.

Defines model classes corresponding to GTFS tables: stops, routes, calendar,
trips, and stop_times.  Each class maps a table and declares column types,
primary keys, foreign-key constraints, and relationship attributes so that
SQLAlchemy can navigate the object graph (e.g. ``trip.route`` or
``stop.stop_times``).

Time columns (arrival_time / departure_time) are stored as TEXT (HH:MM:SS) but
each ``StopTime`` exposes a convenience property that returns the value in
seconds since midnight - useful for aggregate queries.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import ForeignKey, Integer, Float, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Declarative base for all GTFS model classes."""


# ---------------------------------------------------------------------------
# Stops
# ---------------------------------------------------------------------------

class Stop(Base):
    __tablename__ = "stops"

    stop_id: Mapped[str] = mapped_column(String, primary_key=True)
    stop_code: Mapped[str] = mapped_column(String, nullable=False)
    stop_name: Mapped[str] = mapped_column(String, nullable=False)
    stop_lat: Mapped[float] = mapped_column(Float, nullable=False)
    stop_lon: Mapped[float] = mapped_column(Float, nullable=False)

    # Relationships
    stop_times: Mapped[list[StopTime]] = relationship(
        "StopTime", back_populates="stop", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Stop(id={self.stop_id!r}, name={self.stop_name!r})>"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

class Route(Base):
    __tablename__ = "routes"

    route_id: Mapped[str] = mapped_column(String, primary_key=True)
    agency_id: Mapped[str] = mapped_column(String, nullable=False)
    route_short_name: Mapped[str] = mapped_column(String, nullable=False)
    route_long_name: Mapped[str] = mapped_column(String, nullable=False)
    route_desc: Mapped[Optional[str]] = mapped_column(String)
    route_type: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships
    trips: Mapped[list[Trip]] = relationship(
        "Trip", back_populates="route", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Route(id={self.route_id!r}, short={self.route_short_name!r})>"


# ---------------------------------------------------------------------------
# Calendar
# ---------------------------------------------------------------------------

class Calendar(Base):
    __tablename__ = "calendar"

    service_id: Mapped[str] = mapped_column(String, primary_key=True)
    monday: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tuesday: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    wednesday: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    thursday: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    friday: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    saturday: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sunday: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    start_date: Mapped[str] = mapped_column(String, nullable=False)
    end_date: Mapped[str] = mapped_column(String, nullable=False)

    # Relationships
    trips: Mapped[list[Trip]] = relationship(
        "Trip", back_populates="calendar", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Calendar(service_id={self.service_id!r})>"


# ---------------------------------------------------------------------------
# Trips
# ---------------------------------------------------------------------------

class Trip(Base):
    __tablename__ = "trips"

    trip_id: Mapped[str] = mapped_column(String, primary_key=True)
    route_id: Mapped[str] = mapped_column(
        String, ForeignKey("routes.route_id"), nullable=False
    )
    service_id: Mapped[str] = mapped_column(
        String, ForeignKey("calendar.service_id"), nullable=False
    )
    trip_headsign: Mapped[Optional[str]] = mapped_column(String)
    direction_id: Mapped[Optional[int]] = mapped_column(Integer)

    # Relationships
    route: Mapped[Route] = relationship("Route", back_populates="trips")
    calendar: Mapped[Calendar] = relationship("Calendar", back_populates="trips")
    stop_times: Mapped[list[StopTime]] = relationship(
        "StopTime", back_populates="trip", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Trip(id={self.trip_id!r}, headsign={self.trip_headsign!r})>"


# ---------------------------------------------------------------------------
# Stop times
# ---------------------------------------------------------------------------

class StopTime(Base):
    __tablename__ = "stop_times"

    trip_id: Mapped[str] = mapped_column(
        String, ForeignKey("trips.trip_id"), primary_key=True
    )
    stop_sequence: Mapped[int] = mapped_column(Integer, primary_key=True)
    arrival_time: Mapped[str] = mapped_column(String, nullable=False)
    departure_time: Mapped[str] = mapped_column(String, nullable=False)
    stop_id: Mapped[str] = mapped_column(
        String, ForeignKey("stops.stop_id"), nullable=False
    )

    # Relationships
    trip: Mapped[Trip] = relationship("Trip", back_populates="stop_times")
    stop: Mapped[Stop] = relationship("Stop", back_populates="stop_times")

    # -- Helpers ---------------------------------------------------------------

    @property
    def arrival_seconds(self) -> int:
        """Arrival time converted to seconds since midnight."""
        return _time_to_seconds(self.arrival_time)

    @property
    def departure_seconds(self) -> int:
        """Departure time converted to seconds since midnight."""
        return _time_to_seconds(self.departure_time)

    def __repr__(self) -> str:
        return (
            f"<StopTime(trip={self.trip_id!r}, seq={self.stop_sequence}, "
            f"stop={self.stop_id!r})>"
        )


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def _time_to_seconds(hhmmss: str) -> int:
    """Convert a ``HH:MM:SS`` string to seconds since midnight.

    GTFS allows hour values >= 24 (e.g. ``25:30:00`` for a 1:30 AM departure
    past midnight); this function handles those correctly.
    """
    parts = hhmmss.split(":")
    return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
