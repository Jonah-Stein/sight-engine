from typing import NamedTuple
from datetime import datetime
from enums import AircraftSide
class FlightSummaryRequest(NamedTuple):
    day: int
    month: int
    year: int
    airline: str = None
    flight_number: str = None
    outbound_airport: str = None
    inbound_airport: str = None

class TrackingPoint(NamedTuple):
    timestamp: datetime
    lat: float
    lon: float 
    alt: int # feet
    gspeed: int # knots
    direction: int

class MaxSightPoint(NamedTuple):
    lat: float
    lon: float
    aircraft_side: AircraftSide 

class CalculateMaxSightPointsResponse(NamedTuple):
    right: MaxSightPoint
    left: MaxSightPoint
