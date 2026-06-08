from __future__ import annotations

from pathlib import Path

from .models import HttpLogBrowserState


DEFAULT_LOG_PATH = Path(__file__).resolve().parents[2] / "data" / "http_first_100k.log"


def build_default_state(log_path: str | Path | None = None) -> HttpLogBrowserState:
	state = HttpLogBrowserState()
	state.load_from_path(log_path or DEFAULT_LOG_PATH)
	return state


def main() -> int:
	state = build_default_state()
	print(f"Loaded {state.total_count} log entries from {DEFAULT_LOG_PATH}")
	if state.selected_record is not None:
		print(f"First entry: {state.selected_record.preview()}")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
