from __future__ import annotations

import io
import sys
from datetime import datetime, timezone, timedelta

import pytest

from lista8 import utils

from .support import BASE_TS, make_tuple_log


def test_read_log_parses_stdin_into_tuples(monkeypatch: pytest.MonkeyPatch) -> None:
    sample = (
        "1331901000.000000\tuid\t192.168.0.1\t123\t192.168.0.2\t80\t1\tGET\t"
        "host\t/index.html\t-\tUA\t0\t0\t200\tOK\t-\t-\t-\t(empty)\t-\t-\t-\t-\t-\t-\t-\n"
    )
    monkeypatch.setattr(sys, "stdin", io.StringIO(sample))

    logs = utils.read_log()

    assert len(logs) == 1
    assert logs[0][0] == datetime.fromtimestamp(1331901000.0, tz=timezone.utc)
    assert logs[0][6] == "GET"
    assert logs[0][9] == 200


def test_sort_log_and_basic_filters() -> None:
    logs = make_tuple_log()

    sorted_logs = utils.sort_log(logs, 0)
    assert sorted_logs[0][1] == "u1"
    assert sorted_logs[-1][1] == "u2"

    assert utils.get_entries_by_code(logs, 404)[0][1] == "u1"
    assert utils.get_entries_by_extension(logs, ".json")[0][8] == "/api/data.json"
    assert utils.get_entries_in_time_range(logs, BASE_TS, BASE_TS + timedelta(seconds=10)) == logs[:2]


def test_validation_and_summary_helpers(capsys: pytest.CaptureFixture[str]) -> None:
    logs = make_tuple_log()

    assert utils.validate_ip("10.0.0.1") is None
    with pytest.raises(ValueError):
        utils.validate_ip("999.0.0.1")

    assert utils.get_entries_by_addr(logs, "10.0.0.1") == logs[:2]
    assert utils.get_failed_reads(logs, merge=True) == logs[1:]
    assert utils.get_failed_reads(logs) == (logs[1:2], logs[2:])
    assert utils.get_top_ips(logs, n=2) == [("10.0.0.1", 2), ("20.0.0.1", 2)]
    assert utils.get_unique_methods(logs) == ["GET", "POST"]
    assert utils.count_by_method(logs) == {"GET": 2, "POST": 1}
    assert utils.get_top_uris(logs, n=2) == [
        ("/index.html", 1),
        ("/api/data.json", 1),
    ]
    assert utils.count_status_classes(logs) == {
        "1xx": 0,
        "2xx": 1,
        "3xx": 0,
        "4xx": 1,
        "5xx": 1,
    }
    assert utils.entry_to_dict(logs[0])["uid"] == "u1"
    assert utils.most_active_uid(utils.log_to_dict(logs)) == ("u1", 2)
    assert utils.get_session_paths(logs)["u1"] == ["/index.html", "/api/data.json"]
    assert utils.get_extension_stats(logs) == {"html": 1, "json": 1, "png": 1}

    utils.print_dict_entry_dates(utils.log_to_dict(logs))
    out = capsys.readouterr().out
    assert "UID: u1" in out
    assert "2xx to all: 50.00%" in out


def test_detect_sus_and_analyze_log() -> None:
    logs = make_tuple_log()

    suspicious = utils.detect_sus(logs, threshold=1.0, weights=(1.0, 2.0, 0.5))
    assert "10.0.0.1" in suspicious
    assert suspicious["10.0.0.1"]["errors_404"] == 1
    assert suspicious["10.0.0.1"]["fast_retries"] == 1

    summary = utils.analyze_log(logs)
    assert summary["top_ips"][0] == ("10.0.0.1", 2)
    assert summary["top_uris"][0] == ("/index.html", 1)
    assert summary["method_counts"] == {"GET": 2, "POST": 1}
    assert summary["error_count"] == 2
    assert summary["status_class_counts"] == {
        "1xx": 0,
        "2xx": 1,
        "3xx": 0,
        "4xx": 1,
        "5xx": 1,
    }
    assert summary["uid_count"] == 2
