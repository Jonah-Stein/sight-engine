from data_objects import MaxSightPoint, TrackingPoint, CalculateMaxSightPointsResponse
import json
import math
from enums import AircraftSide
from constants import MAX_VISIBILITY_DISTANCE, EARTH_RADIUS
from geopy.distance import distance

def load_flight_path_data(file_path):
    with open(file_path, "r") as f:
        path_data = json.load(f)
    path_data = path_data[0]["tracks"]

    # Convert to TrackingPoint types
    path_data = list(map(lambda x: TrackingPoint(x["timestamp"], x["lat"], x["lon"], x["alt"], x["gspeed"], x["track"]), path_data))
    return path_data

def get_max_sight_points(flight_path: list[TrackingPoint]):
    points = []
    for tracking_point in flight_path:
        max_sight = calculate_max_sight_points(tracking_point)
        points.append(max_sight.right)
        points.append(max_sight.left)
    
    return points

def calculate_max_sight_points(tracking_point: TrackingPoint, aircraft_side: AircraftSide = None):
    # How do I want to calculate this
    # 1: Orthogonal is easy
    right_direction = (tracking_point.direction - 90) % 360
    left_direction = (tracking_point.direction + 90) % 360

    # 2: Calculate sight by taking visibility distance and altitude in feet
    # Take smaller of horizon view and normal pythagorean approach
    horizon_limit = math.sqrt(2*tracking_point.alt*EARTH_RADIUS)
    pure_sight_limit = math.sqrt(tracking_point.alt**2 + MAX_VISIBILITY_DISTANCE**2)
    sight_distance =min(horizon_limit, pure_sight_limit) / 5280.0
    print(horizon_limit)
    print(pure_sight_limit)
    
    
    right_sight_point = tuple(distance(miles=sight_distance).destination((tracking_point.lat, tracking_point.lon), bearing=right_direction))
    left_sight_point = tuple(distance(miles=sight_distance).destination((tracking_point.lat, tracking_point.lon), bearing=left_direction))

    right_point = MaxSightPoint(right_sight_point[0], right_sight_point[1], AircraftSide.RIGHT.value)
    left_point = MaxSightPoint(left_sight_point[0], left_sight_point[1], AircraftSide.LEFT.value)

    return CalculateMaxSightPointsResponse(right_point,left_point)


if __name__ == '__main__':
    file_path = "data/380ce8ef_tracking_data.json"
    flight_path = load_flight_path_data(file_path)

    sight_points = {"sightPoints": get_max_sight_points(flight_path)}
    print(sight_points)
    with open("data/test_sight_points.json", "w") as f:
        json.dump(sight_points, f, indent=2)

