import argparse
import logging
import random
import statistics
import sys
from datetime import datetime

from lista5.parser import EnvironmentalDataset, parse_environmental_data

class StdoutLogFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno <= logging.WARNING

def configure_logger() -> logging.Logger:
    logger = logging.getLogger("AirQualityCLI")
    logger.setLevel(logging.DEBUG)

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.DEBUG)
    stdout_handler.addFilter(StdoutLogFilter())
    stdout_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))

    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.ERROR)
    stderr_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))

    logger.addHandler(stdout_handler)
    logger.addHandler(stderr_handler)

    return logger

def validate_date_format(date_string: str) -> str:
    try:
        datetime.strptime(date_string, "%Y-%m-%d")
        return date_string
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid date format: {date_string}. Expected YYYY-MM-DD.")

def validate_measured_quantity(quantity: str) -> str:
    valid_quantities = {"PM2.5", "PM10", "NO", "NO2", "O3", "CO", "SO2", "BENZEN"}
    quantity_upper = quantity.upper()
    if quantity_upper not in valid_quantities:
        raise argparse.ArgumentTypeError(f"Unsupported quantity: {quantity}. Expected one of {valid_quantities}.")
    return quantity_upper

def execute_random_station(args: argparse.Namespace, dataset: EnvironmentalDataset, logger: logging.Logger) -> None:
    matching_sensors = {
        sensor_id: sensor for sensor_id, sensor in dataset.sensors.items()
        if sensor.indicator == args.quantity and sensor.averaging_time == args.frequency
    }

    if not matching_sensors:
        logger.warning(f"No available sensors found for '{args.quantity}' at '{args.frequency}' frequency.")
        return

    start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
    end_date = datetime.strptime(args.end_date, "%Y-%m-%d")
    
    active_station_ids = set()

    for obs in dataset.observations:
        if start_date <= obs.datetime <= end_date:
            for sensor_id, value in obs.measurements.items():
                if value is not None and sensor_id in matching_sensors:
                    station_id = matching_sensors[sensor_id].station
                    active_station_ids.add(station_id)

    valid_stations = [sid for sid in active_station_ids if sid in dataset.stations]

    if not valid_stations:
        logger.warning("No available measurements for the specified parameters in the given time range.")
        return

    selected_station_id = random.choice(valid_stations)
    station = dataset.stations[selected_station_id]

    print(f"Station Name: {station.station_name}")
    print(f"Address: {station.city}, {station.address}")

def execute_stats(args: argparse.Namespace, dataset: EnvironmentalDataset, logger: logging.Logger) -> None:
    target_sensor_id = None
    for sensor_id, sensor in dataset.sensors.items():
        if (sensor.station == args.station_code and 
            sensor.indicator == args.quantity and 
            sensor.averaging_time == args.frequency):
            target_sensor_id = sensor_id
            break

    if not target_sensor_id:
        logger.warning(f"Frequency '{args.frequency}' or quantity '{args.quantity}' is not supported by station '{args.station_code}'.")
        return

    start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
    end_date = datetime.strptime(args.end_date, "%Y-%m-%d")
    extracted_values = []

    for obs in dataset.observations:
        if start_date <= obs.datetime <= end_date:
            val = obs.measurements.get(target_sensor_id)
            if val is not None:
                extracted_values.append(val)

    if not extracted_values:
        logger.warning(f"No valid measurements found for station '{args.station_code}' in the given time range.")
        return

    mean_value = statistics.mean(extracted_values)
    std_value = statistics.stdev(extracted_values) if len(extracted_values) > 1 else 0.0

    print(f"Mean: {mean_value:.2f}")
    print(f"Standard Deviation: {std_value:.2f}")

def build_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Air Quality Data CLI")
    
    parser.add_argument("--quantity", type=validate_measured_quantity, default="pm10")
    parser.add_argument("--frequency", default="24g")
    parser.add_argument("--start-date", type=validate_date_format, default="2023-01-01")
    parser.add_argument("--end-date", type=validate_date_format, default="2023-05-01")
    parser.add_argument("--measurements-dir", default="data/measurements")
    parser.add_argument("--stations-file", default="data/stacje.csv")

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("random-station")
    
    stats_parser = subparsers.add_parser("stats")
    stats_parser.add_argument("--station-code", default="DsGlogWiStwo")

    return parser

def main() -> None:
    logger = configure_logger()
    parser = build_cli_parser()
    
    try:
        args = parser.parse_args()
    except SystemExit as e:
        logger.error("CLI Argument Parsing Failed.")
        sys.exit(e.code)

    try:
        logger.info("Parsing dataset...")
        dataset = parse_environmental_data(args.measurements_dir, args.stations_file)
    except FileNotFoundError as e:
        logger.error(f"Critical error: Directory or file not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Unexpected critical error during parsing: {e}")
        sys.exit(1)

    if args.command == "random-station":
        execute_random_station(args, dataset, logger)
    elif args.command == "stats":
        execute_stats(args, dataset, logger)

if __name__ == "__main__":
    main()