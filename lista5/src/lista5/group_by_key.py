import os
from pathlib import Path
import re


def group_measurement_files_by_key(dirpath: Path) -> dict[tuple[str, str, str], Path]:
    result = {}
    
    for filename in os.listdir(dirpath):
        path = dirpath / filename
        if not path.is_file():
            continue
        
        if filename.endswith('.csv'):
            match = re.match(r'(\d{4})_(\w+)_(\w+)\.csv', filename)
            if match:
                year, quantity, freq = match.groups()
                if (year, quantity, freq) in result:
                    print(f"Duplicate key found: {(year, quantity, freq)}. Skipping file: {filename}")
                    continue
                result[(year, quantity, freq)] = path
    return result