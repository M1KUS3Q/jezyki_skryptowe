from __future__ import annotations
import sys
from pathlib import Path

from lista8.models import HttpLogBrowserState
from PyQt6.QtWidgets import QApplication
from lista8.gui import LogBrowserWindow


DEFAULT_LOG_PATH = Path(__file__).resolve().parents[2] / "data" / "http_first_100k.log"


def build_default_state(log_path: str | Path | None = None) -> HttpLogBrowserState:
	state = HttpLogBrowserState()
	state.load_from_path(log_path or DEFAULT_LOG_PATH)
	return state


def main() -> int:
    app = QApplication(sys.argv)
    window = LogBrowserWindow()
    window.show()
    return app.exec()

if __name__ == "__main__":
    raise SystemExit(main())
