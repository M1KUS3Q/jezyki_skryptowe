import csv

def parse_metadata(filepath) -> dict[str, list[str]]:
    file = open(filepath, 'r', encoding='utf-8')
    reader = csv.reader(file)
    
    headers = next(reader, [])
    result = []
    
    for row in reader:
        if not row:
            continue
        result.append(dict(zip(headers, row)))
    
    file.close()
    return result

def parse_measurements(file) -> list[dict[str, str]]:
    reader = csv.reader(file)
    
    # First 5 rows contain metadata (?)
    for _ in range(5):
        row = next(reader, None)
                
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
        
    return data