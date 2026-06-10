from lista9.time_series import TimeSeries
from lista9.validator import Anomaly, SeriesValidator

class OutlierDetector(SeriesValidator):    
    def __init__(self, threshold: float) -> None:
        self.max_stdevs_from_mean: float = threshold
    
    def analyze(self, series: TimeSeries) -> list[Anomaly]:
        mean = series.mean
        stdev = series.stddev
        if mean is None or stdev is None:
            return []

        anomalies: list[Anomaly] = []
        for i in range(len(series.values)):
            value = series.values[i]
            if value is None:
                continue
            
            if abs(value - mean) > self.max_stdevs_from_mean * stdev:
                anomalies.append(f"Outlier at index {i}: {value}")
        return anomalies
