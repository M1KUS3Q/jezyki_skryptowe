
from lista5.time_series import TimeSeries
from lista5.validator import SeriesValidator, Anomaly


class ThresholdDetector(SeriesValidator):
    threshold: float
    
    def __init__(self, threshold: float):
        self.threshold = threshold

    def analyze(self, series: TimeSeries) -> list[Anomaly]:
        anomalies = []
        for timestamp, value in zip(series.dates, series.values):
            if value is None:
                continue
            
            if value > self.threshold:
                anomalies.append(f"Value {value} at {timestamp} exceeds threshold {self.threshold}")
        return anomalies