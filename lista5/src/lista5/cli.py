from argparse import ArgumentParser
import os
from pathlib import Path
from pprint import pprint

from lista5.group_by_key import group_measurement_files_by_key
from lista5.parser import parse_measurements, parse_metadata


def cli_csv():
    parser = ArgumentParser()
    parser.add_argument("folderpath", help="Path to the folder containing CSV files (stacje.csv and measurements/)")
    args = parser.parse_args()
    
    folderpath = Path(args.folderpath)
    
    stacje_filepath = folderpath / "stacje.csv"
    measurements_folder = folderpath / "measurements"
    
    metadata = parse_metadata(stacje_filepath)
    print("Metadata:")
    pprint(metadata)
    
    for measurement_file in os.listdir(measurements_folder):
        if measurement_file.endswith(".csv"):
            with open(measurements_folder / measurement_file, "r", encoding='utf-8') as f:
                data = parse_measurements(f)
                print(f"\nData for {measurement_file}:")
                for row in data[:5]:  # Print first 5 rows of data
                    pprint(row)
    
    # args = parser.parse_args()
    # file = open(args.file, "r")
    
    # metadata, data = parse_measurements(file)
    # print("Metadata:")
    # pprint(metadata)
    
    # print("\nData:")
    # for row in data[:5]:  # Print first 5 rows of data
    #     pprint(row)

    # file.close()
    
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
    cli_csv()