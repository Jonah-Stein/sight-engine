import json
import os
from data_objects import FlightSummaryRequest
from fr24_api import FlightRadar24Api
from data_objects import FlightSummaryRequest



api =FlightRadar24Api() 
def test_connection():
    return api.get_account_usage() 

def save_flight_tracking(flight_id):
    flight_tracks = api.get_flight_path(flight_id)
    with open(f"data/{flight_id}_tracking_data.json", "w") as f:
        json.dump(flight_tracks.json(), f, indent=2) 
    return flight_tracks

def get_flight_id(flight: FlightSummaryRequest):
    flight_data =api.get_flight_summary(flight).json()
    with open(f"data/{flight.year}-{flight.month}-{flight.day}-{flight.flight_number}-flights.json", "w") as f:
        json.dump(flight_data, f, indent=2)
    
    # Flight data will return back a list of flights that fit the parameters
    # We'll just assume that the first flight is correct
    return flight_data["data"][0]["fr24_id"]

if __name__ == "__main__":
    sample_flight_data = {
        "airline": "UAL",
        "flight_number": "UAL123",
        "day": 5,
        "month": 6,
        "year": 2025,
        "outbound_airport": "LGA",
        "inbound_airport": "RDU" 
    }
    flight_summary_params = FlightSummaryRequest(**sample_flight_data)
    # Accept tags for flightnumber/id, year, date, month
    # airline_code = input("Airline code (i.e 'UAL', 'AA'): ")
    # flight_number = input("Flight number: ")
    # year = int(input("What year did you take your flight?: "))
    # month = int(input("What month did you take you flight?: "))
    # day = int(input("What day did you take your flight?: "))
    # print(f"{year}-{month}-{day}")

    # print(f"airline_code:{airline_code}")

    flight_id = get_flight_id(flight_summary_params)
    print(flight_id)

    print("getting flight tracking")
    save_flight_tracking(flight_id)

    print("flight tracking saved")
    