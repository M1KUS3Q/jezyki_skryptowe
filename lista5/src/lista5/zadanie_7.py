from lista5.measurements import Measurements
from lista5.validator import OutlierDetector, ThresholdDetector, ZeroSpikeDetector, SeriesValidator
from lista5.validator.simple_reporter import SimpleReporter


if __name__ == "__main__":
    measurements = Measurements("data/measurements") 
    
    validators: list[SeriesValidator] = [
        OutlierDetector(5),
        ThresholdDetector(500),
        ZeroSpikeDetector(),
        SimpleReporter()
    ]
    
    result = measurements.detect_all_anomalies(validators, preload=True)
    
    for (station_code, quantity), anomalies in result.items():
        if anomalies == []:
            continue
        
        print(f"Station: {station_code}, Quantity: {quantity}")
        
        for anomaly in anomalies:
            print(f"  - {anomaly}")
    