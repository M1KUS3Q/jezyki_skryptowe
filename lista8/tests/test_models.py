from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

from lista8.models import HttpLogBrowserState, TimeRange, normalize_datetime

from .support import BASE_TS, make_record_list


def test_browser_state_selection_and_navigation() -> None:
    state = HttpLogBrowserState()
    records = make_record_list()
    state.load_records(records)

    assert state.total_count == 3
    assert state.visible_count == 3
    assert state.selected_index == 0
    assert state.selected_record == records[0]
    assert state.can_select_previous is False
    assert state.can_select_next is True

    assert state.master_items()[0].endswith("...")
    detail = state.detail()
    assert detail is not None
    assert detail["uid"] == "u1"

    assert state.select_next() == records[1]
    assert state.selected_record == records[1]
    assert state.can_select_previous is True
    assert state.can_select_next is True

    assert state.select_previous() == records[0]
    assert state.selected_record == records[0]


def test_time_filter_preserves_selection_when_record_is_visible() -> None:
    state = HttpLogBrowserState()
    records = make_record_list()
    state.load_records(records)
    state.select_index(1)

    filtered = state.filter_by_time_range(records[1].timestamp, records[2].timestamp)

    assert filtered == records[1:]
    assert state.visible_records == records[1:]
    assert state.selected_record == records[1]
    assert state.can_select_previous is False
    assert state.can_select_next is True


def test_time_filter_reselects_first_visible_record_when_needed() -> None:
    state = HttpLogBrowserState()
    records = make_record_list()
    state.load_records(records)
    state.select_index(0)

    state.filter_by_time_range(records[1].timestamp, records[2].timestamp)

    assert state.selected_record == records[1]
    assert state.selected_index == 0


def test_normalize_datetime_and_time_range_validation() -> None:
    normalized = normalize_datetime("2024-01-01T12:00:00")
    assert normalized is not None
    assert normalized.tzinfo == timezone.utc

    assert normalize_datetime(date(2024, 1, 1)).hour == 0
    assert normalize_datetime(datetime(2024, 1, 1, 12, 0, 0)) == datetime(
        2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc
    )

    time_range = TimeRange(records_start := BASE_TS, records_end := BASE_TS)
    assert time_range.contains(BASE_TS)

    with pytest.raises(ValueError):
        TimeRange(records_end, records_start - timezone.utc.utcoffset(BASE_TS))
