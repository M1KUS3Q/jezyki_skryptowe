import pytest

from lista9.anomalies import detect_anomalies
from lista9.time_series import TimeSeries
from lista9.validator.outlier_detector import OutlierDetector
from lista9.validator.threshold_detector import ThresholdDetector
from lista9.validator.zero_spike import ZeroSpikeDetector


class SimpleReporter:
    def detect(self, ts: 'TimeSeries') -> list[str]:
        return [f"Simple report: {len(ts)} measurements analized"]

@pytest.fixture
def anomaly_ts(sample_dates):
    return TimeSeries(dates=sample_dates, values=[150.0, 10.0, 0.0, None, 0.0])

@pytest.mark.parametrize("analyzer, expected_messages_count", [
    (OutlierDetector(k=2), 1),
    (ZeroSpikeDetector(), 1),
    (ThresholdDetector(threshold=100.0), 1),
    (SimpleReporter(), 1)
])
def test_detect_all_anomalies_polymorphism(anomaly_ts, analyzer, expected_messages_count):
    results = detect_anomalies(anomaly_ts, [analyzer])
    
    assert isinstance(results, list), "function should return list of messages"
    assert len(results) == expected_messages_count
    
    for msg in results:
        assert isinstance(msg, str), "Every message should be a str"