from lista9.time_series import TimeSeries
from lista9.validator.outlier_detector import OutlierDetector
from lista9.validator.threshold_detector import ThresholdDetector
from lista9.validator.zero_spike import ZeroSpikeDetector


def test_outlier_detector(sample_dates):
    ts = TimeSeries(dates=sample_dates, values=[10.0, 10.0, 10.0, 10.0, 100.0])
    detector = OutlierDetector(k=3)
    anomalies = detector.detect(ts)
    
    assert len(anomalies) > 0
    assert any("100.0" in str(msg) for msg in anomalies)

def test_zero_spike_detector(sample_dates):
    ts = TimeSeries(dates=sample_dates, values=[12.0, 0.0, None, 0.0, 14.0])
    detector = ZeroSpikeDetector()
    anomalies = detector.detect(ts)
    
    assert len(anomalies) == 1

def test_threshold_detector(sample_dates):
    ts = TimeSeries(dates=sample_dates, values=[50.0, 150.0, 80.0, 200.0, 10.0])
    detector = ThresholdDetector(threshold=100.0)
    anomalies = detector.detect(ts)
    
    assert len(anomalies) == 2