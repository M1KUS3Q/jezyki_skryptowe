from lista9.measurements import Measurements
from lista9.time_series import TimeSeries
from lista9.validator import Anomaly, OutlierDetector, ThresholdDetector, ZeroSpikeDetector, SeriesValidator


class SimpleReporter(SeriesValidator):
    def analyze(self, series: TimeSeries) -> list[Anomaly]:
        result_str: Anomaly = f"Info: {series.indicator} at {series.station_code} has mean {series.mean}"
        return [result_str]
    
if __name__ == "__main__":
    time_series = Measurements("data/measurements").get_by_parameter("PM10")[0]

    analyzers: list[SeriesValidator] = [OutlierDetector(5), ThresholdDetector(500), ZeroSpikeDetector(), SimpleReporter()]
    
    for analyzer in analyzers:
        anomalies = analyzer.analyze(time_series)
        for anomaly in anomalies:
            print(anomaly)