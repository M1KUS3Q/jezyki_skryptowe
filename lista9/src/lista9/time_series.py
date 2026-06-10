import datetime
import statistics

# Measurements of one indicator for one station
class TimeSeries:
    def __init__(self) -> None:
        self.indicator: str = ""
        self.averaging_time: str = ""
        self.unit: str = ""
        self.station_code: str = ""
        self.dates: list[datetime.date | datetime.datetime] = []
        self.values: list[float | None] = []
    
    @property
    def mean(self) -> float | None:
        if not self.values:
            return None
        return sum(x for x in self.values if x is not None) / sum(1 for x in self.values if x is not None)
    
    @property
    def stddev(self) -> float | None:
        if not self.values:
            return None
        return statistics.stdev(x for x in self.values if x is not None)
    
    def __getitem__(self, key: int | slice | datetime.date | datetime.datetime) -> list[tuple[datetime.date | datetime.datetime, float | None]]:
        if isinstance(key, int | slice):
            if isinstance(key, int):
                return [(self.dates[key], self.values[key])]
            return list(zip(self.dates[key], self.values[key]))
        
        if isinstance(key, datetime.date | datetime.datetime):
            result: list[tuple[datetime.date | datetime.datetime, float | None]] = []
            for date, value in zip(self.dates, self.values):
                if date == key:
                    result.append((date, value))
            if result:                
                return result
            raise KeyError(f"Date {key} not found in time series")
        
        raise TypeError(f"Invalid key type: {type(key)}.")