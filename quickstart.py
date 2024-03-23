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


def get_lessons_info(month, year, control_str = ""):
  """
  Returns a list containing different info partaining to the lessons
  taught in a given month/year.

  Arguments:
    month (int)       : month for which to create dictionary for (e.g. for March enter 3).
    year (int)        : year for which to create dictionary for (e.g. for 2024 enter 2024).
    control_str (str) : the function will check for the specified string in the event name, and only treat
                        it as a lesson if the control string is present. The control string will be removed
                        from the event name, leaving only the student's name.

  Returns:
    lessons_info (list : list containing sublists made of a lesson's date, student and duration.
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
    _, days = calendar.monthrange(year, month)

    start = datetime.datetime(year, month, 1).isoformat() + "Z"
    end = datetime.datetime(year, month, days).isoformat() + "Z"

    lessons_info = []

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

    # Gather data for list
    for event in events:
      if control_str in event["summary"]:
        # Get student name from event summary
        stripped_str = event["summary"][len(control_str):]
        split_str = stripped_str.split(" ")
        student = split_str[0]
        
        # Get lesson date, time and duration
        start = event["start"].get("dateTime", event["start"].get("date"))
        start = datetime.datetime.fromisoformat(start)
        end = event["end"].get("dateTime", event["end"].get("date"))
        end = datetime.datetime.fromisoformat(end)

        duration = end.time().hour - start.time().hour + (end.time().minute - start.time().minute) / 60

        # Adds info to list 
        lessons_info.append([start.date().strftime('%d/%m/%Y'), student, duration])

    return lessons_info

  except HttpError as error:
    print(f"An error occurred: {error}")