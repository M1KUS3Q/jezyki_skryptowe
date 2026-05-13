import datetime
import statistics

# Measurements of one indicator for one station
class TimeSeries:
    indicator: str
    averaging_time: str
    unit: str
    dates = []
    values = []
    
    @property
    def mean(self):        
        if not self.values:
            return None
        return sum(self.values) / len(self.values)
    
    @property
    def stddev(self):
        if not self.values:
            return None
        return statistics.stdev(self.values)
    
    def __getitem__(self, key):
        if isinstance(key, int | slice):
            return zip(self.dates[key], self.values[key])
        
        if isinstance(key, datetime.date | datetime.datetime):
            result = []
            for date, value in zip(self.dates, self.values):
                if date == key:
                    result.append((date, value))
            if result:                
                return result
            raise KeyError(f"Date {key} not found in time series")
        
        raise TypeError(f"Invalid key type: {type(key)}.")