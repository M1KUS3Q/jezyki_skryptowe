from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timezone
from pathlib import Path

from .log_parser import HttpLogRecord, load_http_log_file


def normalize_datetime(value: datetime | date | str | None) -> datetime | None:
	if value is None:
		return None

	if isinstance(value, str):
		value = datetime.fromisoformat(value)

	if isinstance(value, date) and not isinstance(value, datetime):
		value = datetime.combine(value, time.min)

	if value.tzinfo is None:
		return value.replace(tzinfo=timezone.utc)

	return value.astimezone(timezone.utc)


@dataclass(slots=True)
class TimeRange:
	start: datetime | None = None
	end: datetime | None = None

	def __post_init__(self) -> None:
		self.start = normalize_datetime(self.start)
		self.end = normalize_datetime(self.end)

		if self.start is not None and self.end is not None and self.start > self.end:
			raise ValueError("start must not be greater than end")

	def contains(self, timestamp: datetime) -> bool:
		timestamp = normalize_datetime(timestamp) or timestamp
		if self.start is not None and timestamp < self.start:
			return False
		if self.end is not None and timestamp > self.end:
			return False
		return True


@dataclass(slots=True)
class HttpLogBrowserState:
	records: list[HttpLogRecord] = field(default_factory=list)
	visible_records: list[HttpLogRecord] = field(default_factory=list)
	selected_index: int | None = None
	time_range: TimeRange | None = None

	@classmethod
	def from_path(cls, path: str | Path) -> HttpLogBrowserState:
		state = cls()
		state.load_from_path(path)
		return state

	def load_from_path(self, path: str | Path) -> None:
		self.load_records(load_http_log_file(path))

	def load_records(self, records: list[HttpLogRecord]) -> None:
		self.records = list(records)
		self._refresh_visible_records()

	def set_time_range(
		self,
		start: datetime | date | str | None,
		end: datetime | date | str | None,
	) -> None:
		self.time_range = TimeRange(start, end)
		self._refresh_visible_records()

	def clear_time_range(self) -> None:
		self.time_range = None
		self._refresh_visible_records()

	def _refresh_visible_records(self) -> None:
		previous_selection = self.selected_record

		if self.time_range is None:
			self.visible_records = list(self.records)
		else:
			self.visible_records = [
				record
				for record in self.records
				if self.time_range.contains(record.timestamp)
			]

		if previous_selection in self.visible_records:
			self.selected_index = self.visible_records.index(previous_selection)
		else:
			self.selected_index = 0 if self.visible_records else None

	@property
	def total_count(self) -> int:
		return len(self.records)

	@property
	def visible_count(self) -> int:
		return len(self.visible_records)

	@property
	def selected_record(self) -> HttpLogRecord | None:
		if self.selected_index is None:
			return None
		if not 0 <= self.selected_index < len(self.visible_records):
			return None
		return self.visible_records[self.selected_index]

	@property
	def can_select_previous(self) -> bool:
		return self.selected_index is not None and self.selected_index > 0

	@property
	def can_select_next(self) -> bool:
		return (
			self.selected_index is not None
			and self.selected_index < len(self.visible_records) - 1
		)

	def select_index(self, index: int) -> HttpLogRecord:
		if not 0 <= index < len(self.visible_records):
			raise IndexError("visible record index out of range")

		self.selected_index = index
		return self.visible_records[index]

	def select_record(self, record: HttpLogRecord) -> HttpLogRecord:
		index = self.visible_records.index(record)
		self.selected_index = index
		return record

	def select_first(self) -> HttpLogRecord | None:
		if not self.visible_records:
			self.selected_index = None
			return None

		self.selected_index = 0
		return self.visible_records[0]

	def select_previous(self) -> HttpLogRecord | None:
		if not self.can_select_previous:
			return None

		return self.select_index(self.selected_index - 1)

	def select_next(self) -> HttpLogRecord | None:
		if not self.can_select_next:
			return None

		return self.select_index(self.selected_index + 1)

	def master_items(self, max_length: int = 30) -> list[str]:
		return [record.preview(max_length=max_length) for record in self.visible_records]

	def detail(self) -> dict[str, object] | None:
		record = self.selected_record
		if record is None:
			return None

		return record.detail_map()

	def current_position(self) -> tuple[int | None, int]:
		return self.selected_index, self.visible_count

	def filter_by_time_range(
		self,
		start: datetime | date | str | None,
		end: datetime | date | str | None,
	) -> list[HttpLogRecord]:
		self.set_time_range(start, end)
		return list(self.visible_records)


def load_browser_state(path: str | Path) -> HttpLogBrowserState:
	return HttpLogBrowserState.from_path(path)
