import datetime
import os.path
import google
import calendar

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


def main():
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
          "credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())

  try:
    service = build("calendar", "v3", credentials=creds)

    # Call the Calendar API
    month = datetime.datetime.today().month
    year = 2024

    _, days = calendar.monthrange(year, month)

    start = datetime.datetime(year, month, 1).isoformat() + "Z"
    end = datetime.datetime(year, month, days).isoformat() + "Z"

    lesson_dates = []
    lesson_info = []

    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=start,
            timeMax=end,
        )
        .execute()
    )
    events = events_result.get("items", [])

    # Prints all the lessons taught alongside their date and duration
    for event in events:
      if "Mr Sahil with " in event["summary"]:
        start = event["start"].get("dateTime", event["start"].get("date"))
        start = datetime.datetime.fromisoformat(start)
        end = event["end"].get("dateTime", event["end"].get("date"))
        end = datetime.datetime.fromisoformat(end)

        duration = end.time().hour - start.time().hour + (end.time().minute - start.time().minute) / 60

        lesson_dates.append(start)
        lesson_info.append([event["summary"], duration])

    all_lessons = dict(zip(lesson_dates, lesson_info))
    return all_lessons

  except HttpError as error:
    print(f"An error occurred: {error}")


if __name__ == "__main__":
  main()