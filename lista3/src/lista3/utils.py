import sys
from datetime import datetime, timezone


def read_log():
    logs = []

    for line in sys.stdin:
        line = line.strip()

        if not line or line.startswith("#"):
            continue  # ignore empty lines

        parts = line.split("\t")
        try:
            ts = datetime.fromtimestamp(float(parts[0]), tz=timezone.utc)
            uid = parts[1]
            orig_h = parts[2]
            orig_p = int(parts[3]) if parts[3] != "-" else None
            resp_h = parts[4]
            resp_p = int(parts[5]) if parts[5] != "-" else None
            method = parts[7]
            host = parts[8]
            uri = parts[9]
            status_code = int(parts[14]) if parts[14] != "-" else None

            log_tuple = (
                ts,
                uid,
                orig_h,
                orig_p,
                resp_h,
                resp_p,
                method,
                host,
                uri,
                status_code,
            )

            logs.append(log_tuple)

        except (ValueError, IndexError):  # ignore incorrect lines
            continue

    return logs


def sort_log(log, index):
    assert index >= 0 and index < len(log)

    logs_sorted = sorted(log, key=lambda tup: (tup[index] is None, tup[index]))

    return logs_sorted


def get_entries_by_code(log, code):
    STATUS_INDEX = 9
    filtered_logs = filter(lambda entry: entry[STATUS_INDEX] == code, log)

    return filtered_logs


def validate_ip(addr):
    parts: list[str] = addr.split(".")
    if len(parts) != 4:
        raise ValueError(f"Invalid IP address: {addr}")
    for part in parts:
        if not part.isdigit() or not (0 <= int(part) <= 255):
            raise ValueError(f"Invalid IP address: {addr}")


def get_entries_by_addr(log, addr):
    validate_ip(addr)

    ORIG_IP_INDEX = 2
    RESP_IP_INDEX = 4
    filtered_logs = filter(
        lambda entry: entry[ORIG_IP_INDEX] == addr or entry[RESP_IP_INDEX] == addr, log
    )

    return filtered_logs


def get_failed_reads(log, merge=False):
    STATUS_INDEX = 9

    if merge:
        # 4xx or 5xx = >= 400, no codes above 599
        return list(
            filter(
                lambda entry: entry[STATUS_INDEX] is not None
                and entry[STATUS_INDEX] >= 400,
                log,
            )
        )
    else:
        return (
            list(
                filter(
                    lambda entry: entry[STATUS_INDEX] is not None
                    and 400 <= entry[STATUS_INDEX] < 500,
                    log,
                )
            ),
            list(
                filter(
                    lambda entry: entry[STATUS_INDEX] is not None
                    and 500 <= entry[STATUS_INDEX] < 600,
                    log,
                )
            ),
        )


def get_entries_by_extension(log, ext):
    URI_INDEX = 8
    filtered_logs = filter(
        lambda entry: entry[URI_INDEX].split("?")[0].endswith(ext), log
    )

    return filtered_logs


def get_top_ips(log, n=10):
    ORIG_IP_INDEX = 2
    RESP_IP_INDEX = 4

    ip_count = {}

    for entry in log:
        orig_ip = entry[ORIG_IP_INDEX]
        resp_ip = entry[RESP_IP_INDEX]

        ip_count[orig_ip] = ip_count.get(orig_ip, 0) + 1
        ip_count[resp_ip] = ip_count.get(resp_ip, 0) + 1

    sorted_ips = sorted(ip_count.items(), key=lambda item: item[1], reverse=True)

    return sorted_ips[:n]


def get_unique_methods(log):
    METHOD_INDEX = 6
    methods = dict()
    for entry in log:
        method = entry[METHOD_INDEX]
        methods[method] = methods.get(method, 0) + 1

    return filter(lambda method: methods[method] == 1, methods)


def get_entires_in_time_range(log, start, end):
    TS_INDEX = 0
    filtered_logs = filter(lambda entry: start <= entry[TS_INDEX] <= end, log)

    return filtered_logs


def count_by_method(log):
    METHOD_INDEX = 6
    method_count = {}

    for entry in log:
        method = entry[METHOD_INDEX]
        method_count[method] = method_count.get(method, 0) + 1

    return method_count


def get_top_uris(log, n=10):
    URI_INDEX = 8
    uri_count = {}

    for entry in log:
        uri = entry[URI_INDEX].split("?")[0]  # throw out query parameters?
        uri_count[uri] = uri_count.get(uri, 0) + 1

    sorted_uris = sorted(uri_count.items(), key=lambda item: item[1], reverse=True)

    return sorted_uris[:n]


def count_status_classes(log):
    STATUS_INDEX = 9
    status_class_count = {"1xx": 0, "2xx": 0, "3xx": 0, "4xx": 0, "5xx": 0}

    for entry in log:
        status_code = entry[STATUS_INDEX]
        if status_code is None:
            continue

        status_class = f"{status_code // 100}xx"
        status_class_count[status_class] += 1

    return status_class_count


def entry_to_dict(entry):
    keys = [
        "timestamp",
        "uid",
        "orig_h",
        "orig_p",
        "resp_h",
        "resp_p",
        "method",
        "host",
        "uri",
        "status_code",
    ]
    return dict(zip(keys, entry))


def log_to_dict(log):
    UID_INDEX = 1
    res = {}

    for entry in log:
        uid = entry[UID_INDEX]
        if uid not in res:
            res[uid] = []
        res[uid].append(entry_to_dict(entry))

    return res


def print_dict_entry_dates(log_dict):
    for uid, entries in log_dict.items():
        ips = set()
        num_requests = len(entries)
        first_request_timestamp = entries[0]["timestamp"]
        last_request_timestamp = entries[-1]["timestamp"]
        method_counts = {}
        code_counts = {"1xx": 0, "2xx": 0, "3xx": 0, "4xx": 0, "5xx": 0}

        for entry in entries:
            ips.add(entry["orig_h"])
            ips.add(entry["resp_h"])
            ips.add(entry["host"])
            method_counts[entry["method"]] = method_counts.get(entry["method"], 0) + 1

            status = entry["status_code"]
            if status is not None:
                status_class = f"{status // 100}xx"
                code_counts[status_class] += 1

            first_request_timestamp = min(first_request_timestamp, entry["timestamp"])
            last_request_timestamp = max(last_request_timestamp, entry["timestamp"])

        print(
            f"UID: {uid}, IPs: {ips}, Number of requests: {num_requests}, First request: {first_request_timestamp}, Last request: {last_request_timestamp}"
        )

        method_percentages = {
            method: count / num_requests * 100
            for method, count in method_counts.items()
        }

        codes_count = sum(code_counts.values()) or 1  # avoid division by zero

        print(f"Method percentages: {method_percentages}")
        print(f"2xx to all: {code_counts['2xx'] / codes_count * 100:.2f}%")


def most_active_uid(log_dict):
    most_active = None
    max_requests = 0

    for uid, entries in log_dict.items():
        num_requests = len(entries)
        if num_requests > max_requests:
            max_requests = num_requests
            most_active = uid

    return most_active, max_requests


def get_session_paths(log):
    log_dict = log_to_dict(log)
    session_paths = {}

    for uid, entries in log_dict.items():
        paths = []
        for entry in entries:
            paths.append(entry["uri"])
        session_paths[uid] = paths

    return session_paths


def detect_sus(log, threshold):
    ip_count = {}
    for entry in log:
        orig_ip = entry[2]
        ip_count[orig_ip] = ip_count.get(orig_ip, 0) + 1

    suspicious_ips = []
    for ip, count in ip_count.items():
        if count > threshold:
            suspicious_ips.append(ip)
    return suspicious_ips


def get_extension_stats(log):
    ext_count = {}
    for entry in log:
        uri = entry[8]
        ext = uri.split("?")[0].split(".")[-1] if "." in uri else ""
        ext_count[ext] = ext_count.get(ext, 0) + 1
    return ext_count


def analyze_log(log):
    res = {}

    res["top_ips"] = get_top_ips(log)
    res["top_uris"] = get_top_uris(log)
    res["method_counts"] = count_by_method(log)
    res["error_count"] = len(get_failed_reads(log, merge=True))
    res["status_class_counts"] = count_status_classes(log)
    res["uid_count"] = len(set(entry[1] for entry in log))

    return res


if __name__ == "__main__":
    logs = read_log()

    print(most_active_uid(log_to_dict(logs)))
