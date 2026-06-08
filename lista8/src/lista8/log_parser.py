from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator


def _optional_text(value: str) -> str | None:
	if value == "-" or value == "":
		return None
	return value


def _optional_int(value: str) -> int | None:
	if value == "-" or value == "":
		return None
	return int(value)


def _normalize_raw_line(line: str) -> str:
	return line.rstrip("\r\n")


@dataclass(frozen=True, slots=True)
class HttpLogRecord:
	raw_line: str
	timestamp: datetime
	uid: str
	orig_h: str
	orig_p: int | None
	resp_h: str
	resp_p: int | None
	trans_depth: int | None
	method: str
	host: str
	uri: str
	referrer: str | None
	user_agent: str | None
	request_body_len: int | None
	response_body_len: int | None
	status_code: int | None
	status_msg: str | None
	info_code: str | None
	info_msg: str | None
	tags: str | None
	extra_fields: tuple[str, ...] = field(default_factory=tuple)

	@property
	def date(self):
		return self.timestamp.date()

	@property
	def time(self):
		return self.timestamp.time().replace(microsecond=0)

	def preview(self, max_length: int = 30) -> str:
		compact = " ".join(self.raw_line.split())
		if len(compact) <= max_length:
			return compact

		return compact[: max_length - 3].rstrip() + "..."

	def compact_tuple(self) -> tuple[object, ...]:
		return (
			self.timestamp,
			self.uid,
			self.orig_h,
			self.orig_p,
			self.resp_h,
			self.resp_p,
			self.method,
			self.host,
			self.uri,
			self.status_code,
		)

	def detail_map(self) -> dict[str, object]:
		return {
			"timestamp": self.timestamp,
			"date": self.date,
			"time": self.time,
			"uid": self.uid,
			"orig_h": self.orig_h,
			"orig_p": self.orig_p,
			"resp_h": self.resp_h,
			"resp_p": self.resp_p,
			"trans_depth": self.trans_depth,
			"method": self.method,
			"host": self.host,
			"uri": self.uri,
			"referrer": self.referrer,
			"user_agent": self.user_agent,
			"request_body_len": self.request_body_len,
			"response_body_len": self.response_body_len,
			"status_code": self.status_code,
			"status_msg": self.status_msg,
			"info_code": self.info_code,
			"info_msg": self.info_msg,
			"tags": self.tags,
			"extra_fields": self.extra_fields,
		}

	@classmethod
	def from_line(cls, line: str) -> HttpLogRecord | None:
		raw_line = _normalize_raw_line(line)
		stripped = raw_line.strip()
		if not stripped or stripped.startswith("#"):
			return None

		parts = raw_line.split("\t")
		if len(parts) < 16:
			return None

		try:
			timestamp = datetime.fromtimestamp(float(parts[0]), tz=timezone.utc)
		except (TypeError, ValueError):
			return None

		return cls(
			raw_line=raw_line,
			timestamp=timestamp,
			uid=parts[1],
			orig_h=parts[2],
			orig_p=_optional_int(parts[3]),
			resp_h=parts[4],
			resp_p=_optional_int(parts[5]),
			trans_depth=_optional_int(parts[6]),
			method=parts[7],
			host=parts[8],
			uri=parts[9],
			referrer=_optional_text(parts[10]) if len(parts) > 10 else None,
			user_agent=_optional_text(parts[11]) if len(parts) > 11 else None,
			request_body_len=_optional_int(parts[12]) if len(parts) > 12 else None,
			response_body_len=_optional_int(parts[13]) if len(parts) > 13 else None,
			status_code=_optional_int(parts[14]) if len(parts) > 14 else None,
			status_msg=_optional_text(parts[15]) if len(parts) > 15 else None,
			info_code=_optional_text(parts[16]) if len(parts) > 16 else None,
			info_msg=_optional_text(parts[17]) if len(parts) > 17 else None,
			tags=_optional_text(parts[18]) if len(parts) > 18 else None,
			extra_fields=tuple(parts[19:]) if len(parts) > 19 else (),
		)


def iter_http_log_records(lines: Iterable[str]) -> Iterator[HttpLogRecord]:
	for line in lines:
		record = HttpLogRecord.from_line(line)
		if record is not None:
			yield record


def load_http_log_file(path: str | Path) -> list[HttpLogRecord]:
	source = Path(path)
	with source.open("r", encoding="utf-8") as handle:
		return list(iter_http_log_records(handle))


def load_http_log_text(text: str) -> list[HttpLogRecord]:
	return list(iter_http_log_records(text.splitlines()))
