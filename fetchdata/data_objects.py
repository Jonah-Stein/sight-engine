from typing import NamedTuple

class FlightSummaryRequest(NamedTuple):
    day: int
    month: int
    year: int
    airline: str = None
    flight_number: str = None
    outbound_airport: str = None
    inbound_airport: str = None

