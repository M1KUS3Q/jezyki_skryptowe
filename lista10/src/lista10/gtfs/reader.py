"""Shared GTFS data reader - parses CSV files from a ZIP archive or directory.

Returns a dictionary of table-name -> list-of-dicts that both the raw-SQL and
ORM load paths consume, so no parsing logic is duplicated.
"""

from __future__ import annotations

import csv
import io
import zipfile
from pathlib import Path
from typing import Any

# Files we care about from the GTFS bundle.
GTFS_FILES = ["stops", "routes", "calendar", "trips", "stop_times"]


def read_gtfs(path: str | Path) -> dict[str, list[dict[str, Any]]]:
    """Parse a GTFS bundle and return ``{table: [row_dict, …]}``.

    *path* may be a ``.zip`` archive or a directory containing ``.txt`` files.
    Only the five core tables are read; extra files in the bundle are ignored.
    Values are returned as strings - type coercion is the caller's job.
    """
    path = Path(path).resolve()

    if path.is_dir():
        return _read_directory(path)
    if path.suffix.lower() == ".zip":
        return _read_zip(path)

    raise ValueError(f"Not a directory or .zip file: {path}")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _read_directory(dir_path: Path) -> dict[str, list[dict[str, Any]]]:
    """Read each ``<name>.txt`` file from a directory."""
    result: dict[str, list[dict[str, Any]]] = {}
    for name in GTFS_FILES:
        txt_path = dir_path / f"{name}.txt"
        if not txt_path.exists():
            continue
        with open(txt_path, encoding="utf-8-sig") as fh:
            result[name] = _parse_csv(fh)
    return result


def _read_zip(zip_path: Path) -> dict[str, list[dict[str, Any]]]:
    """Extract and parse known ``.txt`` entries from a ZIP archive."""
    result: dict[str, list[dict[str, Any]]] = {}
    with zipfile.ZipFile(zip_path) as zf:
        for name in GTFS_FILES:
            txt_name = f"{name}.txt"
            try:
                info = zf.getinfo(txt_name)
            except KeyError:
                continue
            with zf.open(info) as fh:
                text_wrapper = io.TextIOWrapper(fh, encoding="utf-8-sig")
                result[name] = _parse_csv(text_wrapper)
    return result


def _parse_csv(file_obj: io.TextIOBase) -> list[dict[str, Any]]:
    """Read a CSV file object and return a list of dicts (header -> value)."""
    reader = csv.DictReader(file_obj)
    return [dict(row) for row in reader]
