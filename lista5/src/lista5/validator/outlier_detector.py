from lista5.time_series import TimeSeries
from lista5.validator import Anomaly, SeriesValidator

class OutlierDetector(SeriesValidator):    
    max_stdevs_from_mean: float = 5
    
    def analyze(self, series: TimeSeries) -> list[Anomaly]:
        mean = series.mean
        stdev = series.stddev
        anomalies: list[Anomaly] = []
        for i in range(len(series.values)):
            if series.values[i] is None:
                continue
            
            if abs(series.values[i] - mean) > OutlierDetector.max_stdevs_from_mean * stdev:
                anomalies.append(f"Outlier at index {i}: {series.values[i]}")
        return anomalies
