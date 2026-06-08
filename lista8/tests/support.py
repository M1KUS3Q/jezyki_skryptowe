from __future__ import annotations

from datetime import datetime, timedelta, timezone

from lista8.log_parser import HttpLogRecord

BASE_TS = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


def make_log_line(
    timestamp: datetime = BASE_TS,
    uid: str = "uid",
    orig_h: str = "192.168.0.1",
    orig_p: int | str = 123,
    resp_h: str = "192.168.0.2",
    resp_p: int | str = 80,
    method: str = "GET",
    host: str = "example.com",
    uri: str = "/index.html",
    status_code: int | str = 200,
    status_msg: str = "OK",
) -> str:
    fields = [
        f"{timestamp.timestamp():.6f}",
        uid,
        orig_h,
        str(orig_p),
        resp_h,
        str(resp_p),
        "1",
        method,
        host,
        uri,
        "-",
        "Mozilla/5.0",
        "0",
        "0",
        str(status_code),
        status_msg,
        "-",
        "-",
        "-",
        "(empty)",
        "-",
        "-",
        "-",
        "-",
        "-",
        "-",
        "-",
    ]
    return "\t".join(fields)


def make_record(
    timestamp: datetime = BASE_TS,
    uid: str = "uid",
    orig_h: str = "192.168.0.1",
    orig_p: int | str = 123,
    resp_h: str = "192.168.0.2",
    resp_p: int | str = 80,
    method: str = "GET",
    host: str = "example.com",
    uri: str = "/index.html",
    status_code: int | str = 200,
    status_msg: str = "OK",
) -> HttpLogRecord:
    record = HttpLogRecord.from_line(
        make_log_line(
            timestamp=timestamp,
            uid=uid,
            orig_h=orig_h,
            orig_p=orig_p,
            resp_h=resp_h,
            resp_p=resp_p,
            method=method,
            host=host,
            uri=uri,
            status_code=status_code,
            status_msg=status_msg,
        )
    )
    assert record is not None
    return record


def make_record_list() -> list[HttpLogRecord]:
    return [
        make_record(
            timestamp=BASE_TS,
            uid="u1",
            orig_h="10.0.0.1",
            orig_p=111,
            resp_h="20.0.0.1",
            resp_p=80,
            method="GET",
            host="host-a",
            uri="/index.html",
            status_code=200,
            status_msg="OK",
        ),
        make_record(
            timestamp=BASE_TS + timedelta(seconds=10),
            uid="u1",
            orig_h="10.0.0.1",
            orig_p=112,
            resp_h="20.0.0.1",
            resp_p=80,
            method="POST",
            host="host-a",
            uri="/api/data.json",
            status_code=404,
            status_msg="Not Found",
        ),
        make_record(
            timestamp=BASE_TS + timedelta(seconds=20),
            uid="u2",
            orig_h="10.0.0.2",
            orig_p=113,
            resp_h="20.0.0.2",
            resp_p=80,
            method="GET",
            host="host-b",
            uri="/image.png?x=1",
            status_code=500,
            status_msg="Internal Server Error",
        ),
    ]


def make_tuple_log() -> list[tuple[object, ...]]:
    records = make_record_list()
    return [record.compact_tuple() for record in records]
