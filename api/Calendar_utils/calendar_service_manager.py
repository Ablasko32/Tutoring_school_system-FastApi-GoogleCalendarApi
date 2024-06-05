import os
from typing import Annotated

from fastapi import Depends
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from api.logger import api_logger

SCOPES = ["https://www.googleapis.com/auth/calendar"]


class CalendarServiceManager:
    """Service manager for builidng calendar service, needs creds.json, creates token.json, handles login, logout and service creation"""

    def __init__(self):
        self.token_path = os.path.abspath("api/Credentials/token.json")
        self.creds_path = os.path.abspath("api/Credentials/creds.json")

    def get_credentials(self):
        """Gets OAuth2 credentials."""
        creds = None
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                return None  # if no token service cant be built
        return creds

    def get_calendar_service(self):
        """Builds and returns the calendar service."""
        creds = self.get_credentials()
        if creds is None:
            return None  # If there are no valid credentials, service cannot be built
        try:
            service = build("calendar", "v3", credentials=creds)
            return service
        except Exception as e:
            api_logger.error("Error occurred: %s", e)
            return None

    def login(self):
        """Performs login and builds calendar service."""
        flow = InstalledAppFlow.from_client_secrets_file(self.creds_path, SCOPES)
        creds = flow.run_local_server(port=0)
        with open(self.token_path, "w") as token:
            token.write(creds.to_json())
        try:
            service = build("calendar", "v3", credentials=creds)
            return {"message": "Logged in"}
        except Exception as e:
            api_logger.error("Error occurred: %s", e)
            return {"error": str(e)}

    def logout(self):
        """Removes token.json, logging user out and requiring authorization again."""
        try:
            os.remove(self.token_path)
            return {"message": "logged out"}
        except FileNotFoundError:
            return {"message": "token.json file not found"}
        except Exception as e:
            api_logger.error("Error removing token file: %s", e)
            return {"error": str(e)}


# Dependency injection for creating calendar service, handles login and logout
def get_calendar_service_manager():
    return CalendarServiceManager()


service_dependancy = Annotated[
    CalendarServiceManager, Depends(get_calendar_service_manager)
]
