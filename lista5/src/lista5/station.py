from datetime import datetime
from typing import Optional


class Station:
    station_code: str
    number: int
    international_code: str
    station_name: str
    old_station_code: str
    startup_date: datetime
    closing_date: Optional[datetime]
    station_type: str
    area_type: str
    station_kind: str
    voivodeship: str
    city: str
    address: str
    latitude_n: float
    longitude_e: float
    
    def __init__(self, station_code: str, number: int, international_code: str, station_name: str, old_station_code: str,
                 startup_date: datetime, closing_date: Optional[datetime], station_type: str, area_type: str,
                 station_kind: str, voivodeship: str, city: str, address: str, latitude_n: float, longitude_e: float):
        self.station_code = station_code
        self.number = number
        self.international_code = international_code
        self.station_name = station_name
        self.old_station_code = old_station_code
        self.startup_date = startup_date
        self.closing_date = closing_date
        self.station_type = station_type
        self.area_type = area_type
        self.station_kind = station_kind
        self.voivodeship = voivodeship
        self.city = city
        self.address = address
        self.latitude_n = latitude_n
        self.longitude_e = longitude_e
        
    def __str__(self):
        return f"Station(id={self.station_code}, name={self.station_name}, city={self.city})"
    
    def __repr__(self):
        return (
            f"Station(id={self.station_code!r}, number={self.number!r}, international_code={self.international_code!r}, "
            f"station_name={self.station_name!r}, old_station_code={self.old_station_code!r}, "
            f"startup_date={self.startup_date!r}, closing_date={self.closing_date!r}, "
            f"station_type={self.station_type!r}, area_type={self.area_type!r}, "
            f"station_kind={self.station_kind!r}, voivodeship={self.voivodeship!r}, city={self.city!r}, "
            f"address={self.address!r}, latitude_n={self.latitude_n!r}, longitude_e={self.longitude_e!r})"
        )
        
    def __eq__(self, value):
        if not isinstance(value, Station):
            return False
        return self.station_code == value.station_code