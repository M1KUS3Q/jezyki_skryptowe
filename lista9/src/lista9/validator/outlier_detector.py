from lista9.time_series import TimeSeries
from lista9.validator import Anomaly, SeriesValidator

class OutlierDetector(SeriesValidator):    
    max_stdevs_from_mean: float = 5
    
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
            
            if abs(value - mean) > OutlierDetector.max_stdevs_from_mean * stdev:
                anomalies.append(f"Outlier at index {i}: {value}")
        return anomalies
