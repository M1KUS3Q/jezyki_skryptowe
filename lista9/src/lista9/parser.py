from argparse import ArgumentParser
import csv
import os
from dataclasses import dataclass
from pprint import pprint
from typing import Optional, Dict, List
from datetime import datetime

StationId = str # Id of a station, e.g. ZpWiduBulRyb
SensorId = str # Id of a sensor, e.g. ZpWiduBulRyb-NO2-1g. Station can have multiple sensors.

@dataclass
class StationInfo:
    number: int
    international_code: str
    station_name: str
    old_station_code: str
    startup_date: datetime
    closing_date: Optional[datetime]
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
    datetime: datetime
    measurements: Dict[SensorId, Optional[float]]

@dataclass
class EnvironmentalDataset:
    stations: Dict[StationId, StationInfo]
    sensors: Dict[SensorId, SensorMetadata]
    observations: List[Observation]

def _parse_date(date_str: Optional[str]) -> Optional[datetime]:
    if not date_str:
        return None
    date_str = date_str.strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%y %H:%M", "%m/%d/%y"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None

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
                startup_date=_parse_date(row.get("Data uruchomienia")),
                closing_date=_parse_date(row.get("Data zamknięcia")),
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

def _extract_headers_and_sensors(reader) -> Dict[SensorId, SensorMetadata]:
    meta_rows = {}
    for row in reader:
        if not row or not row[0].strip():
            continue
        row_type = row[0].strip()
        meta_rows[row_type] = row
        if row_type == "Kod stanowiska":
            break

    if "Kod stanowiska" not in meta_rows:
        return {}

    sensor_ids = [sid.strip() for sid in meta_rows["Kod stanowiska"][1:]]
    sensors = {}
    
    for i, sensor_id in enumerate(sensor_ids):
        if not sensor_id:
            continue
        sensors[sensor_id] = SensorMetadata(
            station=meta_rows.get("Kod stacji", [])[i+1].strip() if i+1 < len(meta_rows.get("Kod stacji", [])) else "",
            indicator=meta_rows.get("Wskaźnik", [])[i+1].strip() if i+1 < len(meta_rows.get("Wskaźnik", [])) else "",
            averaging_time=meta_rows.get("Czas uśredniania", [])[i+1].strip() if i+1 < len(meta_rows.get("Czas uśredniania", [])) else "",
            unit=meta_rows.get("Jednostka", [])[i+1].strip() if i+1 < len(meta_rows.get("Jednostka", [])) else "",
        )
    return sensors

def _parse_observations(reader, sensor_ids: List[SensorId], obs_by_datetime: Dict[datetime, Dict[SensorId, Optional[float]]]):
    for row in reader:
        if not row or not row[0].strip():
            continue

        dt = _parse_date(row[0].strip())
        if dt is None:
            continue

        if dt not in obs_by_datetime:
            obs_by_datetime[dt] = {}

        for i, sensor_id in enumerate(sensor_ids):
            if not sensor_id:
                continue
            
            if i + 1 < len(row) and row[i+1].strip():
                val_str = row[i+1].strip()
                obs_by_datetime[dt][sensor_id] = float(val_str.replace(',', '.'))
            elif sensor_id not in obs_by_datetime[dt]:
                obs_by_datetime[dt][sensor_id] = None

def parse_environmental_data(measurements_dir: str, stations_file: str) -> EnvironmentalDataset:
    stations = parse_stations_csv(stations_file)
    sensors: Dict[SensorId, SensorMetadata] = {}
    
    obs_by_datetime: Dict[datetime, Dict[SensorId, Optional[float]]] = {}

    for filename in os.listdir(measurements_dir):
        if not filename.endswith('.csv'):
            continue
            
        if filename in ["2023_Depozycja_1m.csv", "2023_NO2_1g.csv"]:
            continue # skip files with known formatting issues

        filepath = os.path.join(measurements_dir, filename)
        with open(filepath, mode='r', encoding='utf-8') as f:
            reader = csv.reader(f)
            
            file_sensors = _extract_headers_and_sensors(reader)
            if not file_sensors:
                continue
                
            sensors.update(file_sensors)
            _parse_observations(reader, list(file_sensors.keys()), obs_by_datetime)

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
    
    # print out 5 stations, 5 sensors, and 5 observations for verification
    print("Stations:")
    pprint(list(dataset.stations.items())[:5])
    print("\nSensors:")
    pprint(list(dataset.sensors.items())[:5])
    print("\nObservations:")
    pprint(list(map(lambda obs: [obs.datetime, list(obs.measurements.items())[:5]], dataset.observations[:5])))