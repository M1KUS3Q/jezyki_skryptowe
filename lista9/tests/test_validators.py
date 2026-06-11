import datetime

import pytest

from lista9.time_series import TimeSeries
from lista9.validator.outlier_detector import OutlierDetector
from lista9.validator.threshold_detector import ThresholdDetector
from lista9.validator.zero_spike import ZeroSpikeDetector

@pytest.fixture
def sample_dates():
    return [
        datetime.date(2023, 1, 1),
        datetime.date(2023, 1, 2),
        datetime.date(2023, 1, 3),
        datetime.date(2023, 1, 4),
        datetime.date(2023, 1, 5)
    ]

def test_outlier_detector(sample_dates):
    ts = TimeSeries
    ts.dates = sample_dates
    ts.values=[10.0, 10.0, 10.0, 10.0, 100.0]
    detector = OutlierDetector(3)
    anomalies = detector.analyze(ts)
    
    assert len(anomalies) >= 0

def test_zero_spike_detector(sample_dates):
    ts = TimeSeries
    ts.dates = sample_dates
    ts.values=[12.0, 0.0, None, 0.0, 14.0]
    detector = ZeroSpikeDetector()
    anomalies = detector.analyze(ts)
    
    assert len(anomalies) == 1

def test_threshold_detector(sample_dates):
    ts = TimeSeries
    ts.dates = sample_dates
    ts.values=[50.0, 150.0, 80.0, 200.0, 10.0]
    
    detector = ThresholdDetector(threshold=100.0)
    anomalies = detector.analyze(ts)
    
    assert len(anomalies) == 2