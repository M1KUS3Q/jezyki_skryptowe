import sys
import pytest
from pathlib import Path
from src.lista3.utils import (
    read_log,
    sort_log,
    get_entries_by_code,
    validate_ip,
    get_entries_by_addr,
    get_failed_reads,
    get_entries_by_extension,
    get_top_ips,
    count_by_method,
    get_top_uris,
    count_status_classes,
    most_active_uid,
    log_to_dict,
    get_unique_methods,
    get_entires_in_time_range,
    get_session_paths,
    detect_sus,
    get_extension_stats,
    analyze_log,
)

DATA_FILE = Path(__file__).parent.parent / "data" / "http_first_100k.log"


@pytest.fixture(scope="module")
def sample_logs():
    original_stdin = sys.stdin
    try:
        with open(DATA_FILE, "r") as f:
            sys.stdin = f
            logs = read_log()
    finally:
        sys.stdin = original_stdin
    return logs


def test_read_log(sample_logs):
    assert len(sample_logs) > 0
    # verify expected tuple structure
    assert len(sample_logs[0]) == 10


def test_validate_ip():
    # Should not raise exception
    validate_ip("192.168.1.1")
    validate_ip("0.0.0.0")
    validate_ip("255.255.255.255")

    # Should raise exception
    with pytest.raises(ValueError):
        validate_ip("256.0.0.1")
    with pytest.raises(ValueError):
        validate_ip("192.168.1")
    with pytest.raises(ValueError):
        validate_ip("abc.def.ghi.jkl")


def test_sort_log(sample_logs):
    if not sample_logs:
        pytest.skip("No logs to sort")

    # Sort by status code (index 9)
    sorted_logs = sort_log(sample_logs, 9)
    assert len(sorted_logs) == len(sample_logs)

    # Check if actually sorted (handling None values which might be present)
    status_codes = [log[9] for log in sorted_logs if log[9] is not None]
    assert status_codes == sorted(status_codes)


def test_get_entries_by_code(sample_logs):
    code_200_logs = list(get_entries_by_code(sample_logs, 200))
    for log in code_200_logs:
        assert log[9] == 200


def test_get_failed_reads(sample_logs):
    merged_failed = get_failed_reads(sample_logs, merge=True)
    for log in merged_failed:
        assert log[9] >= 400

    split_failed_4xx, split_failed_5xx = get_failed_reads(sample_logs, merge=False)
    for log in split_failed_4xx:
        assert 400 <= log[9] < 500
    for log in split_failed_5xx:
        assert 500 <= log[9] < 600


def test_count_by_method(sample_logs):
    method_counts = count_by_method(sample_logs)
    assert isinstance(method_counts, dict)

    # sum of all method counts should equal total logs
    assert sum(method_counts.values()) == len(sample_logs)


def test_get_top_ips(sample_logs):
    top_ips = list(get_top_ips(sample_logs, n=5))
    assert len(top_ips) <= 5
    # Should be sorted
    counts = [count for _, count in top_ips]
    assert counts == sorted(counts, reverse=True)


def test_most_active_uid(sample_logs):
    log_dict = log_to_dict(sample_logs)
    uid, count = most_active_uid(log_dict)

    if log_dict:
        assert uid is not None
        assert count > 0


def test_get_entries_by_addr(sample_logs):
    if not sample_logs:
        pytest.skip("No logs to search")
    # Finding a valid IP from the first entry to test with
    test_ip = sample_logs[0][2]

    entries = list(get_entries_by_addr(sample_logs, test_ip))
    assert len(entries) > 0
    for entry in entries:
        assert entry[2] == test_ip or entry[4] == test_ip


def test_get_entries_by_extension(sample_logs):
    # Test checking for typical image requests (.gif, .png etc.)
    entries = list(get_entries_by_extension(sample_logs, ".gif"))
    for entry in entries:
        assert entry[8].split("?")[0].endswith(".gif")


def test_get_top_uris(sample_logs):
    top_uris = get_top_uris(sample_logs, 5)
    assert len(top_uris) <= 5
    counts = [count for _, count in top_uris]
    assert counts == sorted(counts, reverse=True)


def test_count_status_classes(sample_logs):
    counts = count_status_classes(sample_logs)
    assert isinstance(counts, dict)
    assert "2xx" in counts
    assert "4xx" in counts
    assert "5xx" in counts


def test_get_unique_methods(sample_logs):
    unique_methods = list(get_unique_methods(sample_logs))
    assert isinstance(unique_methods, list)


def test_get_entires_in_time_range(sample_logs):
    if len(sample_logs) < 2:
        pytest.skip("Not enough logs to test time range")

    start_time = sample_logs[0][0]
    end_time = sample_logs[-1][0]

    entries = list(
        get_entires_in_time_range(
            sample_logs, min(start_time, end_time), max(start_time, end_time)
        )
    )
    assert len(entries) > 0
    for entry in entries:
        assert min(start_time, end_time) <= entry[0] <= max(start_time, end_time)


def test_log_to_dict(sample_logs):
    log_dict = log_to_dict(sample_logs)
    assert isinstance(log_dict, dict)
    if sample_logs:
        assert len(log_dict) > 0


def test_get_session_paths(sample_logs):
    paths = get_session_paths(sample_logs)
    assert isinstance(paths, dict)


def test_detect_sus(sample_logs):
    # Pass a high threshold so nothing fails, it just returns a list
    sus_ips = detect_sus(sample_logs, 1000)
    assert isinstance(sus_ips, list)


def test_get_extension_stats(sample_logs):
    stats = get_extension_stats(sample_logs)
    assert isinstance(stats, dict)


def test_analyze_log(sample_logs):
    analysis = analyze_log(sample_logs)
    assert "top_ips" in analysis
    assert "top_uris" in analysis
    assert "method_counts" in analysis
    assert "error_count" in analysis
    assert "status_class_counts" in analysis
    assert "uid_count" in analysis
