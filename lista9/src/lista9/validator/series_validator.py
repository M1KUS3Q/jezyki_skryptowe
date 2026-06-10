from abc import ABC, abstractmethod

from lista9.time_series import TimeSeries

type Anomaly = str

class SeriesValidator(ABC):
    @abstractmethod
    def analyze(self, series: TimeSeries) -> list[Anomaly]:
        raise NotImplementedError