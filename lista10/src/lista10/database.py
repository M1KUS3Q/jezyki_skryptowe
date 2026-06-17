"""Database engine, session factory, and schema-creation utilities.

Uses SQLAlchemy ORM - all tables are created from the model definitions in
``lista10.models`` rather than from raw DDL.
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.engine import Engine as EngineType
from sqlalchemy.orm import Session, sessionmaker

from lista10.models import Base


@event.listens_for(Engine, "connect")
def _set_sqlite_pragmas(dbapi_connection, _connection_record):
    """Enable WAL mode and foreign-key checks for every new connection."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def create_engine_for(path: str | Path) -> EngineType:
    """Return a SQLAlchemy engine for the SQLite database at *path*.

    The PRAGMAs registered above are automatically applied to every
    connection.
    """
    db_path = Path(path).resolve()
    return create_engine(f"sqlite:///{db_path}")


def create_session_factory(engine: EngineType) -> sessionmaker[Session]:
    """Return a ``sessionmaker`` bound to *engine*."""
    return sessionmaker(bind=engine)


def create_tables(engine: EngineType) -> None:
    """Create all GTFS tables from the ORM model metadata."""
    Base.metadata.create_all(engine)


def create_database(path: str | Path) -> EngineType:
    """High-level helper: create a fresh database at *path*.

    Removes any existing file first, then creates the engine and all tables.
    Returns the engine (still open - caller should ``.dispose()`` when done).
    """
    db_path = Path(path).resolve()
    db_path.unlink(missing_ok=True)

    engine = create_engine_for(db_path)
    create_tables(engine)
    return engine
