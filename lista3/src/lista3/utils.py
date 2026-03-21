import sys
from datetime import datetime, time, timezone

index_status = 9

def read_log():
    logs = []

    for line in sys.stdin:
        line = line.strip()

        if not line or line.startswith("#"): 
            continue #ignore empty lines


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

        except (ValueError, IndexError): #ignore incorrect lines
            continue

    return logs


def sort_log(log, index):
    assert index >= 0 and index < len(log)

    logs_sorted = sorted(log, key=lambda tup: tup[1])

    return logs_sorted


def get_entries_by_code(log, code):
    filtered_logs = filter(lambda entry: entry[index_status] == code, log) 

    return filtered_logs





if __name__ == "__main__":
    logs = read_log()
    # logs = sort_log(logs, 3)
    logs = tuple(get_entries_by_code(logs, 200))
    for i in range (10):
        print(logs[i])