import datetime

import pytest

from lista9.anomalies import detect_anomalies
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


class SimpleReporter:
    def detect(self, ts: 'TimeSeries') -> list[str]:
        return [f"Simple report: {len(ts)} measurements analized"]

@pytest.fixture
def anomaly_ts(sample_dates):
    values=[150.0, 10.0, 0.0, None, 0.0]

    ts = TimeSeries()
    ts.dates = sample_dates
    ts.values = values
    return ts

