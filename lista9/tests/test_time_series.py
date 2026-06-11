import math

import pytest
import datetime

from lista9.time_series import TimeSeries

@pytest.fixture
def sample_dates():
    return [
        datetime.date(2023, 1, 1),
        datetime.date(2023, 1, 2),
        datetime.date(2023, 1, 3),
        datetime.date(2023, 1, 4),
        datetime.date(2023, 1, 5)
    ]

@pytest.fixture
def complete_ts(sample_dates):
    values = [10.0, 20.0, 30.0, 40.0, 50.0]
    ts = TimeSeries()
    ts.dates = sample_dates
    ts.values = values
    return ts

@pytest.fixture
def missing_data_ts(sample_dates):
    values = [10.0, None, 30.0, None, 50.0]
    ts = TimeSeries()
    ts.dates = sample_dates
    ts.values = values
    return ts

def test_timeseries_getitem_wrong_type(complete_ts):
    with pytest.raises(TypeError):
        _ = complete_ts["2023-01-01"]

def test_timeseries_getitem_int(complete_ts):
    val = complete_ts[2][0]
    assert val[1] == 30.0

def test_timeseries_getitem_slice(complete_ts):
    subset = complete_ts[1:4]
    assert len(subset) == 3
    assert subset[0][1] == 20 and subset[1][1] == 30 and subset[2][1] == 40

def test_timeseries_getitem_existing_date(complete_ts):
    target_date = datetime.date(2023, 1, 2)
    assert complete_ts[target_date][0][1] == 20.0

def test_timeseries_getitem_missing_date(complete_ts):
    missing_date = datetime.date(2025, 1, 1)
    with pytest.raises(KeyError):
        _ = complete_ts[missing_date]


def test_timeseries_stats_complete(complete_ts):
    assert complete_ts.mean == 30.0
    assert math.isclose(complete_ts.stddev, 15.811388, rel_tol=1e-5)

def test_timeseries_stats_with_none(missing_data_ts):
    assert missing_data_ts.mean == 30.0
    assert missing_data_ts.stddev == 20.0