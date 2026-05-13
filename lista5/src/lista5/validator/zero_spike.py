from lista5.time_series import TimeSeries
from lista5.validator import SeriesValidator, Anomaly


class ZeroSpikeDetector(SeriesValidator):
    def analyze(self, series: TimeSeries) -> list[Anomaly]:
        anomalies = []
        
        def check(x):
            return x is None or x == 0.0
        
        # flag anomaly at index i if 3 or more values in [i..] are 0 or None
        # dont flag again if already flagged at index i-1
        for i in range(len(series.values)):
            if check(series.values[i]) and (i == 0 or not check(series.values[i-1])):
                count = 0
                for j in range(i, len(series.values)):
                    if check(series.values[j]):
                        count += 1
                    else:
                        break
                if count >= 3:
                    anomalies.append(f"Zero spike starting at index {i}, length {count}")
        
        return anomalies