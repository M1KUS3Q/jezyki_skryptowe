import csv

def parse_metadata(reader) -> dict[str, list[str]]:
    metadata = {}
    for _ in range(5):
        row = next(reader, None)
        if row and len(row) > 0:
            metadata[row[0]] = row[1:]
    return metadata

def parse_csv(file) -> tuple[dict[str, list[str]], list[dict[str, str]]]:
    reader = csv.reader(file)
    
    metadata = parse_metadata(reader)
        
    # First row after metadata contains the column names (e.g., 'Kod stanowiska')
    headers = next(reader, [])
    
    data = []
    for row in reader:
        if not row:
            continue
        for i, value in enumerate(row):
            # if value is empty, replace it with None
            # if value is convertable to float convert it to float
            if value == "":
                row[i] = None
            else:
                try:
                    row[i] = float(value)
                except ValueError:
                    pass
        
        data.append(dict(zip(headers, row)))
        
    return metadata, data