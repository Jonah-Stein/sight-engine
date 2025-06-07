import requests
from dotenv import load_dotenv
import os
import datetime
load_dotenv()

class AeroApi():
    def __init__(self):
        self.base_url = os.getenv("AERO_API_URL")
        self.headers = {"x-apikey": os.getenv("AERO_API_KEY")}
    
    def get_historical_flight_id(self, flight_number, year, month, day):
        identity = flight_number
        startdate = datetime.date(year, month, day)
        enddate = startdate + datetime.timedelta(1)
        parameters = {
            "start": startdate,
            "end": enddate
        }
        url = f"{self.base_url}/history/flights/{identity}"
        response = requests.get(url, params = parameters, headers=self.headers)
        return response.json()


    def get_historical_flight_path(self, flight_id):
        url = f"{self.base_url}/history/flights/{flight_id}/track"
        response = requests.get(url, headers = self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_account_usage(self):
        url = f"{self.base_url}/account/usage"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()