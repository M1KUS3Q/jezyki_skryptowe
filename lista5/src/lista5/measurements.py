from datetime import datetime
from pathlib import Path
import os
import re

from lista5.time_series import TimeSeries
from lista5.validator import SeriesValidator
from lista5.validator.series_validator import Anomaly

type Quantity = str
type StationCode = str

class Measurements:
    path: Path
    total_series_count = -1
    paths_by_quantity: dict[Quantity, list[Path | dict[StationCode, TimeSeries]]] = {}

    def __init__(self, path):
        self.path = Path(path)
        self.paths_by_quantity = {}

        pattern = r'\d{4}_([^_]+)_(?:1g|24g)\.csv'

        for filename in os.listdir(path):
            if not filename.endswith(".csv"):
                continue

            if filename in ["2023_Depozycja_1m.csv", "2023_NO2_1g.csv", "2023_Jony_PM25_24g.csv", "2023_PrekursoryZielonka_1g.csv"]:
                continue

            match = re.match(pattern, filename)
            if match:
                quantity = match.group(1)
                if quantity not in self.paths_by_quantity:
                    self.paths_by_quantity[quantity] = []
                self.paths_by_quantity[quantity].append(self.path / filename)


    def __len__(self):
        if self.total_series_count == -1:
            self.total_series_count = 0
            for file in os.listdir(self.path):
                if not file.endswith(".csv") or file in ["2023_Depozycja_1m.csv", "2023_NO2_1g.csv", "2023_Jony_PM25_24g.csv", "2023_PrekursoryZielonka_1g.csv"]:
                    continue

                with open(self.path / file) as f:
                    line = f.readline().split(",")
                    self.total_series_count += (len(line) - 1)
            
        return self.total_series_count
    
    def __contains__(self, parameter_name: str):
        return parameter_name in self.paths_by_quantity

    def _load_file(self, path: Path) -> dict[StationCode, 'TimeSeries']:
        series_by_station = {}
        
        with open(path, mode='r', encoding='utf-8') as f:
            headers = {}
            
            # read headers dynamically until "Kod stanowiska"
            for line in f:
                cols = line.strip().split(',')
                if not cols or not cols[0]:
                    continue
                
                row_name = cols[0].strip()
                headers[row_name] = cols
                
                if row_name == "Kod stanowiska":
                    break
            
            indicator_row = headers.get("Wskaźnik", [])
            avg_time_row = headers.get("Czas uśredniania", [])
            unit_row = headers.get("Jednostka", [])
            station_code_row = headers.get("Kod stacji", [])
            
            stations_count = len(station_code_row) - 1
            
            # initialize TimeSeries objects
            for i in range(1, stations_count + 1):
                station_code = station_code_row[i] if i < len(station_code_row) else ""
                if not station_code:
                    continue
                    
                ts = TimeSeries()
                ts.indicator = indicator_row[i] if i < len(indicator_row) else (indicator_row[1] if len(indicator_row) > 1 else "")
                ts.averaging_time = avg_time_row[i] if i < len(avg_time_row) else (avg_time_row[1] if len(avg_time_row) > 1 else "")
                ts.unit = unit_row[i] if i < len(unit_row) else (unit_row[1] if len(unit_row) > 1 else "")
                ts.station_code = station_code
                ts.dates = []
                ts.values = []
                
                series_by_station[station_code] = ts

            for line in f:
                if not line.strip():
                    continue
                    
                cols = line.strip().split(',')
                if not cols[0]:
                    continue
                
                date_str = cols[0][:16] 
                try:
                    dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
                except ValueError:
                    dt = date_str # fallback
                
                for i in range(1, len(cols)):
                    if i > stations_count:
                        break
                    
                    station_code = station_code_row[i] if i < len(station_code_row) else ""
                    if station_code not in series_by_station:
                        continue
                        
                    val_str = cols[i].strip()
                    val = float(val_str.replace(',', '.')) if val_str else None
                    
                    series_by_station[station_code].dates.append(dt)
                    series_by_station[station_code].values.append(val)
                    
        return series_by_station

    def get_by_station(self, station_code: StationCode) -> list['TimeSeries']:
        result = []
        
        for param_name, items in self.paths_by_quantity.items():
            for idx, item in enumerate(items):
                if isinstance(item, Path):
                    # read dynamically until "Kod stacji"
                    station_row = []
                    with open(item, mode='r', encoding='utf-8') as f:
                        for line in f:
                            cols = line.strip().split(',')
                            if cols and cols[0].strip() == "Kod stacji":
                                station_row = cols
                                break
                    
                    if station_code in station_row:
                        # full load only if the station exists in this file
                        loaded_data = self._load_file(item)
                        self.paths_by_quantity[param_name][idx] = loaded_data
                        if station_code in loaded_data:
                            result.append(loaded_data[station_code])
                            
                elif isinstance(item, dict):
                    # file already cached, check dict keys
                    if station_code in item:
                        result.append(item[station_code])
                        
        return result

    def get_by_parameter(self, param_name: Quantity) -> list['TimeSeries']:
        if param_name not in self.paths_by_quantity:
            return []
            
        result = []
        for idx, item in enumerate(self.paths_by_quantity[param_name]):
            if isinstance(item, Path):
                loaded_data = self._load_file(item)
                self.paths_by_quantity[param_name][idx] = loaded_data # Overwrite path with dictionary cache
                result.extend(loaded_data.values())
            elif isinstance(item, dict):
                # already loaded, use from cache
                result.extend(item.values())
                
        return result
    
    def _preload(self):
        for quantity, files in self.paths_by_quantity.items():
            for idx, item in enumerate(files):
                if isinstance(item, Path):
                    loaded_data = self._load_file(item)
                    self.paths_by_quantity[quantity][idx] = loaded_data
                
    def detect_all_anomalies(self, validators: list[SeriesValidator], preload: bool = False) -> dict[tuple[StationCode, Quantity], list[Anomaly]]:
        if preload:
            self._preload()

        anomalies: dict[tuple[StationCode, Quantity], list[Anomaly]] = {}
        for quantity, cache in self.paths_by_quantity.items():
            for series_by_station in cache:
                if not isinstance(series_by_station, dict):
                    continue
                
                for station_code, series in series_by_station.items():
                    if (station_code, quantity) not in anomalies:
                        anomalies[(station_code, quantity)] = []
                    
                    for validator in validators:
                        anomalies[(station_code, quantity)].extend(validator.analyze(series))
                        
        return anomalies

if __name__ == "__main__":
    m = Measurements("data/measurements") 
    print(len(m))
    print("NO2" in m)
    print(m.get_by_parameter("PM10"))
    print(m.get_by_station("DsGlogWiStwo"))