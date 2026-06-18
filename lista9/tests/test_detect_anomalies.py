import datetime

import pytest

from lista9.time_series import TimeSeries
from lista9.validator import SeriesValidator
from lista9.validator.outlier_detector import OutlierDetector
from lista9.validator.threshold_detector import ThresholdDetector
from lista9.validator.zero_spike import ZeroSpikeDetector


def detect_anomalies(ts: TimeSeries, validators: list[SeriesValidator]) -> list[str]:
    """Run each validator against the time series and return a flat list of anomaly messages."""
    results: list[str] = []
    for validator in validators:
        results.extend(validator.analyze(ts))
    return results


@pytest.fixture
def sample_dates() -> list[datetime.date]:
    return [
        datetime.date(2023, 1, 1),
        datetime.date(2023, 1, 2),
        datetime.date(2023, 1, 3),
        datetime.date(2023, 1, 4),
        datetime.date(2023, 1, 5),
    ]


class SimpleReporter(SeriesValidator):
    """A trivial validator that always reports one summary message — used to
    verify that any SeriesValidator implementation works polymorphically."""

    def analyze(self, ts: TimeSeries) -> list[str]:
        return [f"Simple report: {len(ts.values)} measurements analyzed"]


@pytest.fixture
def anomaly_ts(sample_dates: list[datetime.date]) -> TimeSeries:
    values = [150.0, 10.0, 0.0, None, 0.0]

    ts = TimeSeries()
    ts.dates = sample_dates
    ts.values = values
    return ts


@pytest.mark.parametrize("analyzer, expected_messages_count", [
    (OutlierDetector(1.0), 1),
    (ZeroSpikeDetector(), 1),
    (ThresholdDetector(threshold=100.0), 1),
    (SimpleReporter(), 1),
])
def test_detect_all_anomalies_polymorphism(
    anomaly_ts: TimeSeries,
    analyzer: SeriesValidator,
    expected_messages_count: int,
) -> None:
    results = detect_anomalies(anomaly_ts, [analyzer])

    assert isinstance(results, list), "function should return list of messages"
    assert len(results) == expected_messages_count

    for msg in results:
        assert isinstance(msg, str), "Every message should be a str"
