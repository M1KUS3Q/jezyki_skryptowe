from lista9.station import Station


def test_station_equality_same_code():
    station1 = Station(station_code="S1", international_code="abc", longitude_e=0.1)
    station2 = Station(station_code="S1", international_code="c",  longitude_e=0.2)
    assert station1 == station2

def test_station_equality_different_code():
    station1 = Station(station_code=1, international_code="abc", longitude_e=0.1)
    station2 = Station(station_code=2, international_code="abc", longitude_e=0.1)
    assert station1 != station2