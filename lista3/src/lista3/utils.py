import sys
from datetime import datetime, time, timezone

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


if __name__ == "__main__":
    logs = read_log()
    print(logs[0])