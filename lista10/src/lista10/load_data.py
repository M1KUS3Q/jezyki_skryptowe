#!/usr/bin/env python3
"""Load GTFS data into a timetable database (Task 2).

Usage::

    python -m lista10.load_data <gtfs_zip_or_dir> <db_name>           # raw SQL
    python -m lista10.load_data --orm <gtfs_zip_or_dir> <db_name>    # ORM

The database must already exist (created by ``create_database.py``).
Data is loaded in FK-safe order inside a single transaction.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from lista10.gtfs.reader import read_gtfs


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Load GTFS data into a timetable database."
    )
    parser.add_argument(
        "--orm",
        action="store_true",
        help="Use SQLAlchemy ORM instead of raw SQL.",
    )
    parser.add_argument(
        "gtfs_path",
        help="Path to a GTFS .zip archive or directory containing .txt files.",
    )
    parser.add_argument(
        "name",
        help="Database name WITHOUT extension (e.g. 'my_timetable')",
    )
    args = parser.parse_args()

    db_path = Path(f"{args.name}.sqlite3")

    print(f"Reading GTFS data from {args.gtfs_path} ...")
    data = read_gtfs(args.gtfs_path)
    for table, rows in data.items():
        print(f"  {table}: {len(rows)} rows")

    if args.orm:
        from lista10.orm.crud import load_all
        load_all(db_path, data)
    else:
        import sqlite3
        from lista10.raw.crud import load_all
        conn = sqlite3.connect(str(db_path))
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        try:
            load_all(conn, data)
        finally:
            conn.close()

    print(f"Data loaded into {db_path.resolve()}")


if __name__ == "__main__":
    main()
