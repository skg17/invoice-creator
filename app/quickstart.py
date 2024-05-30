import datetime
import os.path
import google
import calendar
import jinja2
import pdfkit
import json

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


def get_lessons_info(month, year):
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
    start = datetime.datetime(year, month, 1).isoformat() + "Z"
    end = datetime.datetime(year, month+1, 1).isoformat() + "Z"

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

    control_str = get_user_settings()["control_str"]

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
        lessons_info.append([start.date(), student, duration])

    return lessons_info

  except HttpError as error:
    print(f"An error occurred: {error}")

def get_user_settings():
  if os.path.isfile('user_settings.json'):
    user_settings = json.load(open('user_settings.json', 'r'))

  else:
    required_settings = ["full_name", "email",
                         "address", "town",
                         "postcode", "control_str",
                         "hourly_rate", "account_no", "sort_code"]
    
    user_settings = {}
    
    for key in required_settings:
       user_settings[key] = input("Please enter {}: ".format(key))

    with open('user_settings.json', 'w') as outfile:
       json.dump(user_settings, outfile)

  return user_settings

def get_lessons(month=None, year=None):
    month = month if month else datetime.datetime.now().month
    year = year if year else datetime.datetime.now().year

    lessons_info = get_lessons_info(month, year)
    hourly_rate = int(get_user_settings()["hourly_rate"])

    for i in range(len(lessons_info)):
        lessons_info[i].append(hourly_rate * lessons_info[i][2])
        lessons_info[i].append(lessons_info[i][0].weekday())
        lessons_info[i][0] = lessons_info[i][0].strftime('%d/%m/%Y')

    lessons_info.sort()

    week = []
    month_lessons = []

    for i in range(len(lessons_info)):
        week.append(lessons_info[i])
        if (i != len(lessons_info)-1) and (lessons_info[i][4] > lessons_info[i+1][4]):
            month_lessons.append(week)
            week = []
        
        elif i == len(lessons_info)-1:
            month_lessons.append(week)

    weekly_total = []

    for week in month_lessons:
        week_total = 0
        
        for day in week:
            week_total += day[3]
            day[3] = "&pound{0:.2f}".format(day[3])
        
        weekly_total.append(week_total)

    return month_lessons, weekly_total

def createPDF(month_lessons, weekly_total):
    i = 0

    head = open('templates/head.html', 'r')
    tail = open('templates/tail.html', 'r')
    new_table = open('templates/new_table.html', 'r').read()
    user_settings = get_user_settings()

    with open('invoice.html', 'a') as f:
        f.write(head.read())
        
        for week in month_lessons:
            f.write(new_table)
            for day in week:
                f.write('\n<tr>')
                f.write('\n<td>{}</td>'.format(day[0]))
                f.write('\n<td>{}</td>'.format(day[1]))
                f.write('\n<td>&pound{0:.2f}</td>'.format(int(user_settings["hourly_rate"])))
                f.write('\n<td>{}</td>'.format(day[2]))
                f.write('\n<td class="bold">{}</td>'.format(day[3]))
                f.write('\n</tr>')

            f.write('\n<tr>')
            f.write('\n<td colspan="4" align="right" class="week-total"><strong>TOTAL DUE FOR WEEK {}</strong></td>'.format(i+1))
            f.write('\n<td class="total"><strong>&pound{0:.2f}</strong></td>'.format(weekly_total[i]))
            f.write('\n')
            i += 1

        f.write('\n')
        f.write(tail.read())

    today_date = datetime.datetime.today().strftime("%d %b, %Y")
    _, month, year = month_lessons[0][0][0].split('/')

    context = {'client_name': user_settings['full_name'].title(),
               'address_line1': user_settings['address'].title(),
               'address_line2': user_settings['town'].title(),
               'invoice_date': today_date,
               'address_line3': user_settings['postcode'].upper(),
               'invoice_no': year + month,
               'user_email': user_settings["email"],
               'account_no': user_settings["account_no"],
               'sort_code': user_settings["sort_code"],
               'monthly_total': "{0:.2f}".format(sum(weekly_total))
    }

    template_loader = jinja2.FileSystemLoader('./')
    template_env = jinja2.Environment(loader=template_loader)

    html_template = 'invoice.html'
    template = template_env.get_template(html_template)
    output_text = template.render(context)

    config = pdfkit.configuration(wkhtmltopdf='')
    output_pdf = 'invoice.pdf'
    pdfkit.from_string(output_text, output_pdf, configuration=config, css='static/css/invoice_styles.css')