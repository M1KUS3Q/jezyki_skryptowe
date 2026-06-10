
from lista9.time_series import TimeSeries
from lista9.validator import SeriesValidator, Anomaly


class ThresholdDetector(SeriesValidator):
    def __init__(self, threshold: float) -> None:
        self.threshold: float = threshold

    def analyze(self, series: TimeSeries) -> list[Anomaly]:
        anomalies: list[Anomaly] = []
        for timestamp, value in zip(series.dates, series.values):
            if value is None:
                continue
            
            if value > self.threshold:
                anomalies.append(f"Value {value} at {timestamp} exceeds threshold {self.threshold}")
        return anomalies