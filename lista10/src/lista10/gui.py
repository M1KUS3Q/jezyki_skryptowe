#!/usr/bin/env python3
"""Flask web GUI for stop timetable queries (Task 3 - ambitious version).

Usage::

    python -m lista10.gui <db_name>

Opens a browser window with:
- A dropdown to select a stop
- Live-updating statistics dashboard (all five query types)
"""

from __future__ import annotations

import argparse
import webbrowser
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from lista10.database import create_engine_for, create_session_factory
from lista10.orm import queries as q


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

def create_app(db_path: str) -> Flask:
    template_dir = str(Path(__file__).resolve().parent / "templates")
    app = Flask(__name__, template_folder=template_dir)

    @app.route("/")
    def index():
        engine = create_engine_for(db_path)
        Session = create_session_factory(engine)
        with Session() as session:
            stops = q.get_all_stops(session)
        engine.dispose()
        return render_template("index.html", stops=stops)

    @app.route("/api/stop/<stop_id>")
    def api_stop(stop_id: str):
        engine = create_engine_for(db_path)
        Session = create_session_factory(engine)
        with Session() as session:
            result = {
                "count_lines": q.count_lines_at_stop(session, stop_id),
                "count_departures": q.count_departures(session, stop_id),
                "earliest": q.earliest_departure(session, stop_id),
                "latest": q.latest_departure(session, stop_id),
                "most_common_directions": q.most_common_directions(session, stop_id),
                "custom_query": q.custom_query(session, stop_id),
            }
        engine.dispose()
        return jsonify(result)

    return app


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Launch the GTFS timetable web GUI."
    )
    parser.add_argument(
        "name",
        help="Database name WITHOUT extension (e.g. 'my_timetable')",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Port to listen on (default: 5000).",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Don't open a browser automatically.",
    )
    args = parser.parse_args()

    db_path = str(Path(f"{args.name}.sqlite3").resolve())
    if not Path(db_path).exists():
        print(f"Database not found: {db_path}")
        return

    app = create_app(db_path)

    if not args.no_browser:
        webbrowser.open(f"http://127.0.0.1:{args.port}")

    print(f"GUI available at http://127.0.0.1:{args.port}")
    app.run(host="127.0.0.1", port=args.port, debug=False)


if __name__ == "__main__":
    main()
