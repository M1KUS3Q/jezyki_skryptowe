from argparse import ArgumentParser
import csv
import os
from dataclasses import dataclass
from pprint import pprint
from typing import Optional, Dict, List

StationId = str # Id of a station, e.g. ZpWiduBulRyb
SensorId = str # Id of a sensor, e.g. ZpWiduBulRyb-NO2-1g. Station can have multiple sensors.

@dataclass
class StationInfo:
    number: int
    international_code: str
    station_name: str
    old_station_code: str
    startup_date: str
    closing_date: Optional[str]
    station_type: str
    area_type: str
    station_kind: str
    voivodeship: str
    city: str
    address: str
    latitude_n: float
    longitude_e: float

@dataclass
class SensorMetadata:
    station: StationId
    indicator: str
    averaging_time: str
    unit: str

@dataclass
class Observation:
    datetime: str
    measurements: Dict[SensorId, Optional[float]]

@dataclass
class EnvironmentalDataset:
    stations: Dict[StationId, StationInfo]
    sensors: Dict[SensorId, SensorMetadata]
    observations: List[Observation]

def parse_stations_csv(filepath: str) -> Dict[StationId, StationInfo]:
    stations: Dict[StationId, StationInfo] = {}
    with open(filepath, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Handle potential whitespace/newline artifacts in the raw CSV header
            old_code_key = next((k for k in row.keys() if k and "Stary Kod" in k), "Stary Kod stacji")
            
            stations[row["Kod stacji"]] = StationInfo(
                number=int(row["Nr"]) if row.get("Nr") else 0,
                international_code=row["Kod międzynarodowy"],
                station_name=row["Nazwa stacji"],
                old_station_code=row.get(old_code_key, ""),
                startup_date=row["Data uruchomienia"],
                closing_date=row["Data zamknięcia"] if row.get("Data zamknięcia") else None,
                station_type=row["Typ stacji"],
                area_type=row["Typ obszaru"],
                station_kind=row["Rodzaj stacji"],
                voivodeship=row["Województwo"],
                city=row["Miejscowość"],
                address=row["Adres"],
                latitude_n=float(row["WGS84 φ N"]) if row.get("WGS84 φ N") else 0.0,
                longitude_e=float(row["WGS84 λ E"]) if row.get("WGS84 λ E") else 0.0
            )
    return stations

def parse_environmental_data(measurements_dir: str, stations_file: str) -> EnvironmentalDataset:
    stations = parse_stations_csv(stations_file)
    sensors: Dict[SensorId, SensorMetadata] = {}
    
    obs_by_datetime: Dict[str, Dict[SensorId, Optional[float]]] = {}

    for filename in os.listdir(measurements_dir):
        if not filename.endswith('.csv'):
            continue
            
        filepath = os.path.join(measurements_dir, filename)
        with open(filepath, mode='r', encoding='utf-8') as f:
            reader = csv.reader(f)

            meta_rows = {}
            for _ in range(10): # read up to 10 rows to find headers
                row = next(reader, None)
                if not row:
                    break
                row_type = row[0].strip().strip(',')
                
                # Handling empty first cell like in Depozycja which has ',Nr'
                if not row_type and len(row) > 1:
                    row_type = row[1].strip()

                if row_type == "Nr":
                    meta_rows["index"] = row
                elif row_type == "Kod stacji":
                    meta_rows["station_code"] = row
                elif row_type == "Wskaźnik":
                    meta_rows["indicator"] = row
                elif row_type == "Czas uśredniania":
                    meta_rows["averaging_time"] = row
                elif row_type == "Jednostka":
                    meta_rows["unit"] = row
                elif row_type == "Kod stanowiska":
                    meta_rows["kod_stanowiska"] = row
                elif row_type in ("Czas pomiaru", "Data od"):
                    meta_rows["station_id"] = row
                    break # Last header row

            if "station_id" not in meta_rows:
                continue

            # Figure out which columns are actual sensors
            # In Depozycja, col 1 is 'Data do' and real sensors start at col 2
            sensor_cols = []
            for col in range(1, len(meta_rows["station_id"])):
                sid = meta_rows["station_id"][col].strip()
                if sid and sid != "Data do":
                    sensor_cols.append(col)

            for col in sensor_cols:
                sensor_id = meta_rows["station_id"][col]
                sensors[sensor_id] = SensorMetadata(
                    station=meta_rows.get("station_code", [])[col] if "station_code" in meta_rows and col < len(meta_rows["station_code"]) else "",
                    indicator=meta_rows.get("indicator", [])[col] if "indicator" in meta_rows and col < len(meta_rows["indicator"]) else "",
                    averaging_time=meta_rows.get("averaging_time", [])[col] if "averaging_time" in meta_rows and col < len(meta_rows["averaging_time"]) else "",
                    unit=meta_rows.get("unit", [])[col] if "unit" in meta_rows and col < len(meta_rows["unit"]) else "",
                )

            for row in reader:
                if not row or not row[0].strip():
                    continue

                dt = row[0].strip()
                if dt not in obs_by_datetime:
                    obs_by_datetime[dt] = {}

                for col in sensor_cols:
                    if col >= len(row):
                        continue
                    
                    station_id = meta_rows["station_id"][col]
                    val_str = row[col].strip()
                    
                    if val_str:
                        # Ensure we convert properly, replacing comma with dot if necessary
                        val_str = val_str.replace(',', '.')
                        obs_by_datetime[dt][station_id] = float(val_str)
                    else:
                        if station_id not in obs_by_datetime[dt]:
                            obs_by_datetime[dt][station_id] = None

    observations = [
        Observation(datetime=dt, measurements=meas) 
        for dt, meas in sorted(obs_by_datetime.items())
    ]

    return EnvironmentalDataset(stations=stations, sensors=sensors, observations=observations)

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("measurements_dir", help="Directory containing measurement CSV files")
    parser.add_argument("stations_file", help="CSV file containing station information")
    args = parser.parse_args()

    dataset = parse_environmental_data(args.measurements_dir, args.stations_file)
    
    pprint(dataset.stations)