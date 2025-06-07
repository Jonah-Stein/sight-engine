import os
import requests
from dotenv import load_dotenv
from data_objects import FlightSummaryRequest
from datetime import date, datetime, timedelta
load_dotenv()
class FlightRadar24Api():
    def __init__(self):
        self.base_url = os.getenv("FR24_API_URL")
        self.api_key = os.getenv("FR24_API_KEY")
        self.headers = {"Accept": "applications/json", "Authorization": f"Bearer {self.api_key}", "Accept-Version": "v1", "API Version": "v1"}
    def get_usage(self):
        url = f"{self.base_url}/usage"
        return requests.get(url, headers =self.headers)

    def get_flight_path(self, flight_id):
        url = f"{self.base_url}/flight-tracks"
        parameters = {"flight_id": flight_id}
        response = requests.get(url, params=parameters, headers=self.headers)
        return response
    
    def get_flight_summary(self, flight: FlightSummaryRequest):

        # Validate that there is enough data
        if not flight.flight_number and not flight.airline and not flight.inbound_airport and not flight.outbound_airport:
            return "error" # Edit this
        starttime = datetime(flight.year, flight.month, flight.day)
        endtime = starttime + timedelta(days=1)

        parameters = {
            "flight_datetime_from" : starttime,
            "flight_datetime_to": endtime,
            "flights": flight.flight_number,
            "operating_as": flight.airline,
            "route": f"{flight.outbound_airport}-{flight.inbound_airport}"
        }

        url = f"{self.base_url}/flight-summary/light"
        print(url)
        response = requests.get(url, params=parameters, headers=self.headers)

        return response
        
        
