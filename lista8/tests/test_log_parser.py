from __future__ import annotations

from lista8.log_parser import HttpLogRecord, load_http_log_text

from .support import BASE_TS, make_log_line


def test_from_line_parses_core_fields_and_preview() -> None:
    record = HttpLogRecord.from_line(make_log_line())

    assert record is not None
    assert record.timestamp == BASE_TS
    assert record.uid == "uid"
    assert record.orig_h == "192.168.0.1"
    assert record.method == "GET"
    assert record.host == "example.com"
    assert record.uri == "/index.html"
    assert record.status_code == 200
    assert record.status_msg == "OK"
    assert record.date.isoformat() == "2024-01-01"
    assert record.time.isoformat() == "12:00:00"

    preview = record.preview()
    assert "\t" not in preview
    assert len(preview) <= 30
    assert preview.endswith("...")

    compact = record.compact_tuple()
    assert compact[0] == BASE_TS
    assert compact[-1] == 200

    detail = record.detail_map()
    assert detail["host"] == "example.com"
    assert detail["tags"] is None
    assert len(detail["extra_fields"]) == 8


def test_load_http_log_text_ignores_comments_and_blank_lines() -> None:
    text = "\n# ignored comment\n\n" + make_log_line() + "\n"

    records = load_http_log_text(text)

    assert len(records) == 1
    assert records[0].uid == "uid"
