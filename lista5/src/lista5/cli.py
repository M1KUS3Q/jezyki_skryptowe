from argparse import ArgumentParser


def cli_csv():
    parser = ArgumentParser()
    parser.add_argument("file", help="CSV file to process")
    
    args = parser.parse_args()
    file = open(args.file, "r")
    
    # TODO: Process the CSV file here

    file.close()
    
if __name__ == "__main__":
    cli_csv()