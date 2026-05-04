from argparse import ArgumentParser
from pathlib import Path
from pprint import pprint

from lista5.group_by_key import group_measurement_files_by_key
from lista5.parser import parse_csv


def cli_csv():
    parser = ArgumentParser()
    parser.add_argument("file", help="CSV file to process")
    
    args = parser.parse_args()
    file = open(args.file, "r")
    
    metadata, data = parse_csv(file)
    print("Metadata:")
    pprint(metadata)
    
    print("\nData:")
    for row in data[:5]:  # Print first 5 rows of data
        pprint(row)

    file.close()
    
def cli_group():
    parser = ArgumentParser()
    parser.add_argument("dir", help="Directory containing CSV files to group")
    
    args = parser.parse_args()
    dirpath = args.dir
    
    pprint(group_measurement_files_by_key(Path(dirpath)))
    
def cli_addresses():
    parser = ArgumentParser()
    parser.add_argument("file", help="CSV file to process")
    parser.add_argument("city", help="City to filter addresses by")
    
    args = parser.parse_args()
    
    from lista5.get_addresses import get_addresses
    addresses = get_addresses(args.file, args.city)
    
    print(f"Addresses in {args.city}:")
    for address in addresses:
        pprint(address)

if __name__ == "__main__":
    cli_addresses()