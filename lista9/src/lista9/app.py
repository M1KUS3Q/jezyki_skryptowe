import sys
import random
import statistics
import logging
from datetime import datetime
from enum import Enum
import typer

from lista5.parser import EnvironmentalDataset, parse_environmental_data

app = typer.Typer(help="environmental data analysis cli tool")

class MeasuredQuantity(Enum):
    pm25 = "PM2.5"
    pm10 = "PM10"
    no = "NO"
    no2 = "NO2"
    o3 = "O3"
    co = "CO"
    so2 = "SO2"
    benzen = "BENZEN"

class StdoutLogFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno <= logging.WARNING

def setup_logger() -> logging.Logger:
    # route logs to stdout/stderr based on severity
    logger = logging.getLogger("env_data_cli")
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

@app.callback()
def load_global_state(
    ctx: typer.Context,
    quantity: MeasuredQuantity = typer.Option(MeasuredQuantity["pm10"], help="pollutant indicator to analyze"),
    frequency: str = typer.Option("24g", help="sensor averaging time, e.g., 1g, 24g"),
    start_date: datetime = typer.Option("2023-01-01", formats=["%Y-%m-%d"], help="filter start date"),
    end_date: datetime = typer.Option("2023-05-01", formats=["%Y-%m-%d"], help="filter end date"),
    measurements_dir: str = typer.Option("data/measurements", help="path to directory with measurements"),
    stations_file: str = typer.Option("data/stacje.csv", help="path to stations metadata file")
):
    # execute once before any subcommand
    logger = setup_logger()
    
    try:
        logger.info("parsing environmental dataset...")
        dataset = parse_environmental_data(measurements_dir, stations_file)
    except FileNotFoundError as err:
        logger.error(f"critical file missing: {err}")
        raise typer.Exit(code=1)
    except Exception as err:
        logger.critical(f"unexpected parsing failure: {err}")
        raise typer.Exit(code=1)

    # inject dependencies to subcommands via context
    ctx.obj = {
        "dataset": dataset,
        "logger": logger,
        "quantity": quantity.value,
        "frequency": frequency,
        "start_date": start_date,
        "end_date": end_date
    }

@app.command("random-station")
def print_random_active_station(ctx: typer.Context):
    # unpack injected state
    state = ctx.obj
    dataset: EnvironmentalDataset = state["dataset"]
    logger: logging.Logger = state["logger"]

    # filter sensors by global criteria
    matching_sensors = {
        sensor_id: sensor for sensor_id, sensor in dataset.sensors.items()
        if sensor.indicator == state["quantity"] and sensor.averaging_time == state["frequency"]
    }

    if not matching_sensors:
        logger.warning(f"no sensors match {state['quantity']} at {state['frequency']}")
        return

    active_station_ids = set()

    # locate active stations within date bounds
    for obs in dataset.observations:
        if state["start_date"] <= obs.datetime <= state["end_date"]:
            for sensor_id, value in obs.measurements.items():
                if value is not None and sensor_id in matching_sensors:
                    active_station_ids.add(matching_sensors[sensor_id].station)

    valid_station_ids = [sid for sid in active_station_ids if sid in dataset.stations]

    if not valid_station_ids:
        logger.warning("no observations found for given parameters")
        return

    random_id = random.choice(valid_station_ids)
    station = dataset.stations[random_id]

    print(f"station name: {station.station_name}")
    print(f"address: {station.city}, {station.address}")

@app.command("stats")
def print_station_statistics(
    ctx: typer.Context,
    station_code: str = typer.Option("DsGlogWiStwo", help="international code of target station")
):
    # unpack injected state
    state = ctx.obj
    dataset: EnvironmentalDataset = state["dataset"]
    logger: logging.Logger = state["logger"]

    # find specific sensor for this station
    target_sensor_id = None
    for sensor_id, sensor in dataset.sensors.items():
        if (sensor.station == station_code and 
            sensor.indicator == state["quantity"] and 
            sensor.averaging_time == state["frequency"]):
            target_sensor_id = sensor_id
            break

    if not target_sensor_id:
        logger.warning(f"station {station_code} lacks {state['quantity']} at {state['frequency']}")
        return

    valid_measurements = []

    # extract measurements in bounds
    for obs in dataset.observations:
        if state["start_date"] <= obs.datetime <= state["end_date"]:
            val = obs.measurements.get(target_sensor_id)
            if val is not None:
                valid_measurements.append(val)

    if not valid_measurements:
        logger.warning(f"no valid data for {station_code} in given timeframe")
        return

    mean_value = statistics.mean(valid_measurements)
    std_value = statistics.stdev(valid_measurements) if len(valid_measurements) > 1 else 0.0

    print(f"mean: {mean_value:.2f}")
    print(f"standard deviation: {std_value:.2f}")

if __name__ == "__main__":
    app()