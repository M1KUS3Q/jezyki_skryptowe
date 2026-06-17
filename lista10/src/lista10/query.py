#!/usr/bin/env python3
"""Interactive stop-timetable query tool (Task 3).

Usage::

    python -m lista10.query <db_name>           # raw SQL (default)
    python -m lista10.query --orm <db_name>     # ORM

Lists all stops, lets the user pick one, then runs all five query types.
"""

from __future__ import annotations

import argparse
import textwrap
from pathlib import Path

# Colour helpers (ANSI escapes - degrade gracefully if redirected)
_CYAN = "\033[96m"
_GREEN = "\033[92m"
_YELLOW = "\033[93m"
_RESET = "\033[0m"
_BOLD = "\033[1m"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Query timetable statistics for a stop."
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
    if not db_path.exists():
        print(f"Database not found: {db_path}")
        return

    if args.orm:
        _run_orm(db_path)
    else:
        _run_raw(db_path)


# ---------------------------------------------------------------------------
# Raw SQL path
# ---------------------------------------------------------------------------

def _run_raw(db_path: Path) -> None:
    import sqlite3
    from lista10.raw import queries as q

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        stops = q.get_all_stops(conn)
        if not stops:
            print("No stops found in database.")
            return

        _show_stop_list(stops)
        stop_id = _pick_stop(stops)

        _print_header(stop_id, stops)
        _print_row("Lines serving this stop", q.count_lines_at_stop(conn, stop_id))
        _print_row("Total departures", q.count_departures(conn, stop_id))
        _print_row("Earliest departure", q.earliest_departure(conn, stop_id))
        _print_row("Latest departure", q.latest_departure(conn, stop_id))

        dirs = q.most_common_directions(conn, stop_id)
        _print_directions(dirs)

        custom = q.custom_query(conn, stop_id)
        _print_custom(custom)
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# ORM path
# ---------------------------------------------------------------------------

def _run_orm(db_path: Path) -> None:
    from lista10.database import create_engine_for, create_session_factory
    from lista10.orm import queries as q

    engine = create_engine_for(db_path)
    Session = create_session_factory(engine)

    with Session() as session:
        stops = q.get_all_stops(session)
        if not stops:
            print("No stops found in database.")
            return

        _show_stop_list(stops)
        stop_id = _pick_stop(stops)

        _print_header(stop_id, stops)
        _print_row("Lines serving this stop", q.count_lines_at_stop(session, stop_id))
        _print_row("Total departures", q.count_departures(session, stop_id))
        _print_row("Earliest departure", q.earliest_departure(session, stop_id))
        _print_row("Latest departure", q.latest_departure(session, stop_id))

        dirs = q.most_common_directions(session, stop_id)
        _print_directions(dirs)

        custom = q.custom_query(session, stop_id)
        _print_custom(custom)

    engine.dispose()


# ---------------------------------------------------------------------------
# Shared UI helpers
# ---------------------------------------------------------------------------

def _show_stop_list(stops: list[dict]) -> None:
    """Print a numbered list of stops."""
    print(f"\n{_BOLD}Available stops:{_RESET}")
    for i, s in enumerate(stops):
        print(f"  {_CYAN}{i:4d}{_RESET}  {s['stop_name'][:40]:40s}  "
              f"({s['stop_code']})")


def _pick_stop(stops: list[dict]) -> str:
    """Let the user pick a stop by index."""
    while True:
        try:
            choice = input(f"\n{_BOLD}Pick a stop number:{_RESET} ").strip()
            idx = int(choice)
            return stops[idx]["stop_id"]
        except (ValueError, IndexError):
            print(f"  Enter a number between 0 and {len(stops) - 1}.")


def _print_header(stop_id: str, stops: list[dict]) -> None:
    name = next((s["stop_name"] for s in stops if s["stop_id"] == stop_id), stop_id)
    print(f"\n{_BOLD}{'=' * 60}{_RESET}")
    print(f"{_BOLD}  Stop: {_GREEN}{name}{_RESET}  ({stop_id})")
    print(f"{_BOLD}{'=' * 60}{_RESET}\n")


def _print_row(label: str, value: object) -> None:
    print(f"  {_YELLOW}{label:30s}{_RESET} {value}")


def _print_directions(dirs: list[dict]) -> None:
    print(f"\n  {_BOLD}Most common directions:{_RESET}")
    if not dirs:
        print("    (none)")
        return
    for d in dirs:
        headsign = d.get("trip_headsign") or "(no headsign)"
        print(f"    {headsign[:50]:50s} {d['cnt']:6d}")


def _print_custom(rows: list[dict]) -> None:
    if not rows:
        print(f"\n  {_BOLD}Custom query:{_RESET} (no data)")
        return

    # Detect which kind of custom query this is
    if "route_short_name" in rows[0]:
        heading = "Top lines at this stop"
        key = "route_short_name"
        label_fmt = "Line: {:<8s}"
    elif "hour" in rows[0]:
        heading = "Departures per hour of day"
        key = "hour"
        label_fmt = "Hour: {:<6s}"
    else:
        heading = "Custom query"
        key = next(iter(rows[0].keys() - {"cnt"}))
        label_fmt = "{}: {:<10s}"

    print(f"\n  {_BOLD}{heading} (custom query):{_RESET}")
    for r in rows:
        val = r[key]
        print(f"    {label_fmt.format(str(val))}  departures: {r['cnt']}")


if __name__ == "__main__":
    main()
