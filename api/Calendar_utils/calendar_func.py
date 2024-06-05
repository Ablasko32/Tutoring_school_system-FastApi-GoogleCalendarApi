import datetime
import os.path

import dotenv
from fastapi import Depends
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from api.logger import api_logger

dotenv.load_dotenv()

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar"]

CALENDAR_ID = os.getenv("CALENDAR_ID")


# def get_calendar_service():
#     """Returns a calendar service, needs creds.json, creates token.json"""
#     creds = None
#     # Check to see if we have token.json
#     if os.path.exists(".api/Credentials/token.json"):
#         creds = Credentials.from_authorized_user_file("Credentials/token.json", SCOPES)
#     # if not token.json proceed with login from creds.json
#     if not creds or not creds.valid:
#         if creds and creds.expired and creds.refresh_token:
#             creds.refresh(Request())
#         else:
#             flow = InstalledAppFlow.from_client_secrets_file(
#                 "./api/Credentials/creds.json", SCOPES
#             )
#             creds = flow.run_local_server(port=0)
#         # Store credetials
#         with open("./api/Credentials/token.json", "w") as token:
#             token.write(creds.to_json())
#
#         try:
#             service = build("calendar", "v3", credentials=creds)
#             return service
#         except HttpError as e:
#             api_logger.error("Error occured: %s", e)


# def get_calendar_service():
#     """Returns a calendar service using service account credentials."""
#     try:
#         credentials = service_account.Credentials.from_service_account_file(
#             "./api/Credentials/service.json", scopes=SCOPES
#         )
#         service = build("calendar", "v3", credentials=credentials)
#         return service
#     except HttpError as e:
#         api_logger.error("Error occurred: %s", e)
#         return None


def add_event_to_calendar(service, name, start_time, end_time, description, frequency):
    """Adds new event to calendar, requires service to be set up first, takes name,start_time,end_time,reccuerence"""

    notifications = [
        {"method": "popup", "minutes": 60},
        {"method": "email", "minutes": 1440},
    ]

    if frequency:
        freq = frequency.freq.upper()
        by_day = frequency.by_day
        weeks = frequency.weeks

        recurrence_end_date = (
            start_time + datetime.timedelta(weeks=weeks - 1, days=4)
        ).strftime("%Y%m%dT%H%M%SZ")

        RRULE = f"RRULE:FREQ={freq};BYDAY={by_day};UNTIL={recurrence_end_date}"
    else:
        RRULE = "RRULE:FREQ=DAILY;COUNT=1"

    event = {
        "summary": name,
        "location": "online",
        "description": description,
        "colorId": 6,
        "start": {
            "dateTime": start_time.isoformat(),
            "timeZone": os.getenv("TIME_ZONE"),
        },
        "end": {
            "dateTime": end_time.isoformat(),  # datetime.datetime(2024, 6, 30, 11, 0).isoformat()
            "timeZone": os.getenv("TIME_ZONE"),
        },
        "recurrence": [RRULE],
        "attendees": [],
    }

    event["reminders"] = {"useDefault": False, "overrides": notifications}

    try:
        event = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
    except HttpError as e:
        api_logger.error("Error with creating event: %s", e)
    api_logger.info("New event created, at event %s", event.get("htmlLink"))
    return event


def add_reservation_to_calendar(service, event_id, new_student_mail):
    """Adds student email to atendees of event/makes a reservation"""

    try:
        target_event = (
            service.events().get(calendarId=CALENDAR_ID, eventId=event_id).execute()
        )
        current_students = target_event.get("attendees", [])
        new_student = {"email": new_student_mail}
        if new_student not in current_students:
            current_students.append(new_student)
            target_event["attendees"] = current_students
            try:
                updated_event = (
                    service.events()
                    .update(calendarId=CALENDAR_ID, eventId=event_id, body=target_event)
                    .execute()
                )
                api_logger.info("Updated event at %s", updated_event.get("htmlLink"))
                return target_event
            except HttpError as e:
                api_logger.error("Error has occured: %s", e)
        else:
            api_logger.error("Student in attendees")
    except HttpError as e:
        api_logger.error("Error has occured: %s", e)


def delete_reservation_from_calendar(service, event_id, target_student_mail):
    """Removes student from atendees"""

    try:
        target_event = (
            service.events().get(calendarId=CALENDAR_ID, eventId=event_id).execute()
        )
        current_attendees = target_event.get("attendees", [])

        for student in current_attendees:
            if student.get("email") == target_student_mail:
                current_attendees.remove(student)
                break
        target_event["attendees"] = current_attendees
        try:
            updated_event = (
                service.events()
                .update(calendarId=CALENDAR_ID, eventId=event_id, body=target_event)
                .execute()
            )
            api_logger.info("Updated event at %s", updated_event.get("htmlLink"))
            return updated_event
        except HttpError as e:
            api_logger.error("Error has occured: %s", e)

    except HttpError as e:
        api_logger.error("Error has occured: %s", e)


def delete_class_from_calendar(service, event_id):
    """Delete class from calendar based on event id"""
    try:
        target_event = (
            service.events().delete(calendarId=CALENDAR_ID, eventId=event_id).execute()
        )
        return target_event
    except HttpError as e:
        api_logger.error("Error has occured: %s", e)


def update_event_calendar(
    service, event_id, name, description, start_time, end_time, frequency
):
    """Updates data for calendar event"""

    notifications = [
        {"method": "popup", "minutes": 60},
        {"method": "email", "minutes": 1440},
    ]
    if frequency:
        freq = frequency.freq.upper()
        by_day = frequency.by_day
        weeks = frequency.weeks

        recurrence_end_date = (
            start_time + datetime.timedelta(weeks=weeks - 1, days=4)
        ).strftime("%Y%m%dT%H%M%SZ")

        RRULE = f"RRULE:FREQ={freq};BYDAY={by_day};UNTIL={recurrence_end_date}"
    else:
        RRULE = "RRULE:FREQ=DAILY;COUNT=1"
    event = {
        "summary": name,
        "location": "online",
        "description": description,
        "colorId": 6,
        "start": {
            "dateTime": start_time.isoformat(),
            "timeZone": os.getenv("TIME_ZONE"),
        },
        "end": {
            "dateTime": end_time.isoformat(),  # datetime.datetime(2024, 6, 30, 11, 0).isoformat()
            "timeZone": os.getenv("TIME_ZONE"),
        },
        "recurrence": [RRULE],
        "attendees": [],
    }
    event["reminders"] = {"useDefault": False, "overrides": notifications}

    try:
        updated_event = (
            service.events()
            .update(calendarId=CALENDAR_ID, eventId=event_id, body=event)
            .execute()
        )
    except HttpError as e:
        api_logger.error("Error with creating event: %s", e)
        api_logger.info("New event created, at event %s", event.get("htmlLink"))
        return event
