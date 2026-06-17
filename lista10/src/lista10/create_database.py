#!/usr/bin/env python3
"""Create an empty GTFS timetable database (Task 1b).

Usage::

    python -m lista10.create_database my_timetable          # raw SQL (default)
    python -m lista10.create_database --orm my_timetable    # ORM / ambitious

Both calls create ``my_timetable.sqlite3`` with the same schema.
"""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create an empty GTFS timetable database."
    )
    parser.add_argument(
        "--orm",
        action="store_true",
        help="Use SQLAlchemy ORM instead of raw SQL.",
    )
    parser.add_argument(
        "name",
        help="Database name WITHOUT extension (e.g. 'my_timetable')",
    )
    args = parser.parse_args()

    db_path = Path(f"{args.name}.sqlite3")

    if args.orm:
        from lista10.orm.crud import create_database
        create_database(db_path)
    else:
        from lista10.raw.crud import create_database
        conn = create_database(db_path)
        conn.close()

    print(f"Created database: {db_path.resolve()}")


if __name__ == "__main__":
    main()
