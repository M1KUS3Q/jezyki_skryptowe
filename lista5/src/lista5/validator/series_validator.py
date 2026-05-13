from abc import ABC, abstractmethod

from lista5.time_series import TimeSeries

type Anomaly = str

class SeriesValidator(ABC):
    @abstractmethod
    def analyze(self, series: TimeSeries) -> list[Anomaly]:
        pass