from argparse import ArgumentParser
from ast import Dict
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from json.encoder import INFINITY
from pprint import pprint
from typing import List, Optional

from lista5.app import MeasuredQuantity
from lista5.parser import EnvironmentalDataset, Observation, SensorId, parse_environmental_data

type ObservationsBySensor = Dict[SensorId, List[tuple[datetime,Optional[float]]]]

@dataclass
class AnomalyDetectionSettings:
    max_delta: float = INFINITY
    max_invalid_value_fraction: float = 1.0
    edge_levels: Dict[MeasuredQuantity, float] | None = None

class AnomalyDetectionReason(Enum):
    MAX_DELTA_EXCEEDED = "max_delta_exceeded"
    INVALID_VALUE_FRACTION_EXCEEDED = "invalid_value_fraction_exceeded"
    EDGE_LEVEL_SURROUNDED_BY_VALID_VALUES = "edge_level_surrounded_by_valid_values"

def group_observation_by_sensor(observations: List[Observation]) -> ObservationsBySensor:
    result: ObservationsBySensor = {}
    
    for obs in observations:
        for sensor_id, value in obs.measurements.items():
            if sensor_id not in result:
                result[sensor_id] = []
            result[sensor_id].append((obs.datetime, value))

    return result

def _delta_exceeds_threshold(values: List[Optional[float]], threshold: float) -> bool:
    for i in range(1, len(values)):
        prev_value = values[i-1]
        curr_value = values[i]
        if prev_value is not None and curr_value is not None:
            delta = abs(curr_value - prev_value)
            if delta > threshold:
                return True
    return False

def _null_percentage(values: List[Optional[float]]) -> float:
    if not values:
        return 0.0
    none_count = sum(1 for v in values if v is None or v <= 0.0)
    return none_count / len(values)

def _corrupt_values(values: List[Optional[float]], edge_level: float) -> bool:
    for i in range(1, len(values)-1):
        prev_value = values[i-1]
        curr_value = values[i]
        next_value = values[i+1]
        
        if curr_value is not None and curr_value >= edge_level:
            if (prev_value is not None and prev_value < edge_level) and (next_value is not None and next_value < edge_level):
                return True
    return False

def detect_anomalies(settings: AnomalyDetectionSettings,dataset: EnvironmentalDataset) -> set[tuple[SensorId, AnomalyDetectionReason]]:
    observations_by_sensor = group_observation_by_sensor(dataset.observations)
    
    corrupted_sensor_ids = set()
    
    for sensor_id, obs_list in observations_by_sensor.items():
        
        # check for max delta
        if settings.max_delta < INFINITY and _delta_exceeds_threshold([val for _, val in obs_list], settings.max_delta):
                corrupted_sensor_ids.add((sensor_id, AnomalyDetectionReason.MAX_DELTA_EXCEEDED))
                continue
            
        # check for invalid value fraction
        if settings.max_invalid_value_fraction < 1.0 and _null_percentage([val for _, val in obs_list]) > settings.max_invalid_value_fraction:
                corrupted_sensor_ids.add((sensor_id, AnomalyDetectionReason.INVALID_VALUE_FRACTION_EXCEEDED))
                continue
        
        # check for edge levels surrounded by valid values
        indicator = dataset.sensors[sensor_id].indicator
        if settings.edge_levels is not None:
            for mq, edge_level in settings.edge_levels.items():
                if indicator == mq.value and _corrupt_values([ val for _, val in obs_list], edge_level):
                        corrupted_sensor_ids.add((sensor_id, AnomalyDetectionReason.EDGE_LEVEL_SURROUNDED_BY_VALID_VALUES))
                        break
    
    return corrupted_sensor_ids
        
    
if __name__ == "__main__":
    parser = ArgumentParser(description="Detect anomalies in environmental sensor data")
    
    parser.add_argument("--data-dir", type=str, default="data/measurements", help="Directory with measurement data")
    parser.add_argument("--stations-file", type=str, default="data/stacje.csv", help="CSV file with station metadata")
    parser.add_argument("--max-delta", type=float, default=INFINITY, help="Maximum allowed delta between consecutive measurements")
    parser.add_argument("--max-invalid-value-fraction", type=float, default=1.0, help="Maximum allowed fraction of invalid (null or non-positive) values")
    parser.add_argument("--edge-levels", type=str, default=None, help="Comma-separated list of indicator=edge_level pairs, e.g. 'pm10=500.0,pm2.5=250.0'")
    
    args = parser.parse_args()
    
    if args.edge_levels is not None:
        edge_levels = {}
        for pair in args.edge_levels.split(","):
            indicator_str, level_str = pair.split("=")
            indicator = MeasuredQuantity(indicator_str.strip().upper())
            level = float(level_str.strip())
            edge_levels[indicator] = level
    else:
        edge_levels = None
        
    settings = AnomalyDetectionSettings(
        max_delta=args.max_delta,
        max_invalid_value_fraction=args.max_invalid_value_fraction,
        edge_levels=edge_levels)
    
    print("Parsed anomaly detection settings:")
    pprint(settings)
    
    
    print("Loading dataset...")
    dataset = parse_environmental_data(args.data_dir, args.stations_file)
    
    count_reason = {reason: 0 for reason in AnomalyDetectionReason}
    for sensor_id, reason in detect_anomalies(settings, dataset):
        count_reason[reason] += 1
        
    print("total corrupted sensors:", sum(count_reason.values()))
    print("total sensors:", len(dataset.sensors))
    print("reason count:")
    for reason in AnomalyDetectionReason:
        print(f"  {reason.value}: {count_reason[reason]}")