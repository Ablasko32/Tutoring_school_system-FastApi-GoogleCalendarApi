import datetime
import os.path
from fastapi import Depends
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from .logger import api_logger

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar"]


def get_calendar_service():
  """Shows basic usage of the Google Calendar API.
  Prints the start and name of the next 10 events on the user's calendar.
  """
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "./api/creds.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("./api/token.json", "w") as token:
      token.write(creds.to_json())

    try:
        service = build("calendar", "v3", credentials=creds)
        return service
    except HttpError as e:
        api_logger.error("Error occured: %s",e)


def add_event_to_calendar(service, name, start_time, end_time):
    """Adds new event to calendar, requires service to be set up first"""

    event = {
        "summary":name,
        "location":"online",
        "description":"description",
        "colorId":6,
        'start': {
            'dateTime': start_time.isoformat(),
            'timeZone': 'Europe/Belgrade',
        },
        'end': {
            'dateTime': end_time.isoformat(),#datetime.datetime(2024, 6, 30, 11, 0).isoformat()
            'timeZone': 'Europe/Belgrade'
        },
        "recurrence":[
            "RRULE:FREQ=DAILY;COUNT=5"
        ],
        "attendees":[
            {"email":"test@mail.com"}
        ]



    }

    event = service.events().insert(calendarId="b0270e623ecc742a735ec9798a0b022aee0242f1780ff006005535220cf6ab88@group.calendar.google.com", body=event).execute()
    api_logger.info("New event created, at event %s", event.get("htmlLink"))


