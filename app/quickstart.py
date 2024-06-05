import datetime
import os
import json
import calendar
import jinja2
import pdfkit
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Constants
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"
USER_SETTINGS_FILE = 'user_settings.json'
HTML_TEMPLATE_FILE = 'invoices/html/invoice.html'
CSS_FILE = 'static/css/invoice_styles.css'
HEAD_TEMPLATE = 'templates/head.html'
TAIL_TEMPLATE = 'templates/tail.html'
NEW_TABLE_TEMPLATE = 'templates/new_table.html'

# Fetch user settings
def get_user_settings():
    if os.path.isfile(USER_SETTINGS_FILE):
        with open(USER_SETTINGS_FILE, 'r') as file:
            user_settings = json.load(file)
    else:
        required_settings = ["full_name", "email", "address", "town", "postcode",
                             "control_str", "hourly_rate", "account_no", "sort_code"]
        
        user_settings = {key: input(f"Please enter {' '.join(key.split('_'))}: ") for key in required_settings}

        with open(USER_SETTINGS_FILE, 'w') as outfile:
            json.dump(user_settings, outfile)

    return user_settings

USER_SETTINGS = get_user_settings()

# Fetch Google credentials
def get_google_credentials():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return creds

# Fetch lessons info
def get_lessons_info(month, year):
    creds = get_google_credentials()

    try:
        service = build("calendar", "v3", credentials=creds)
        time_min = datetime.datetime(year, month, 1).isoformat() + "Z"
        time_max = datetime.datetime(year, month + 1, 1).isoformat() + "Z"

        events_result = service.events().list(
            calendarId="primary", timeMin=time_min, timeMax=time_max, maxResults=1000, singleEvents=True,
            orderBy="startTime"
        ).execute()

        events = events_result.get("items", [])
        control_str = USER_SETTINGS["control_str"]
        
        lessons_info = [
            [datetime.datetime.fromisoformat(event["start"].get("dateTime", event["start"].get("date"))).date(),
             get_student_name(control_str, event),
             (datetime.datetime.fromisoformat(event["end"].get("dateTime", event["end"].get("date"))).time().hour -
              datetime.datetime.fromisoformat(event["start"].get("dateTime", event["start"].get("date"))).time().hour +
              (datetime.datetime.fromisoformat(event["end"].get("dateTime", event["end"].get("date"))).time().minute -
               datetime.datetime.fromisoformat(event["start"].get("dateTime", event["start"].get("date"))).time().minute) / 60)]
            for event in events
        ]

        return lessons_info
    
    except HttpError as error:
        print(f"An error occurred: {error}")
        return []

# Group lessons info by weeks
def group_lessons(month, year):
    lessons_info = get_lessons_info(month, year)
    hourly_rate = float(USER_SETTINGS["hourly_rate"])

    for lesson in lessons_info:
        lesson.append(hourly_rate * lesson[2])
        lesson.append(lesson[0].weekday())
        lesson[0] = lesson[0].strftime('%d/%m/%Y')

    lessons_info.sort()
    month_lessons = []
    week = []

    for i, lesson in enumerate(lessons_info):
        week.append(lesson)

        if i != len(lessons_info) - 1 and lesson[4] > lessons_info[i + 1][4]:
            month_lessons.append(week)
            week = []

        elif i == len(lessons_info) - 1:
            month_lessons.append(week)

    weekly_totals = [sum(day[3] for day in week) for week in month_lessons]

    for week in month_lessons:
        for day in week:
            day[3] = f"&pound{day[3]:.2f}"

    return month_lessons, weekly_totals

# Get student name from event
def get_student_name(control_str, event):
    stripped_str = event["summary"].replace(control_str, "").strip()
    student, *_ = stripped_str.split(" ")

    return student

# Create HTML file for invoice
def create_html(month_lessons, weekly_totals):
    hourly_rate = USER_SETTINGS["hourly_rate"]

    with open(HEAD_TEMPLATE, 'r') as head_file, open(TAIL_TEMPLATE, 'r') as tail_file, open(NEW_TABLE_TEMPLATE, 'r') as table_file:
        with open(HTML_TEMPLATE_FILE, 'w') as invoice_file:
            invoice_file.write(head_file.read())
            table_template = table_file.read()

            for i, week in enumerate(month_lessons):
                invoice_file.write(table_template)

                for day in week:
                    invoice_file.write(f'\n<tr><td>{day[0]}</td><td>{day[1]}</td><td>&pound{hourly_rate:.2f}</td><td>{day[2]}</td><td class="bold">{day[3]}</td></tr>')
                invoice_file.write(f'\n<tr><td colspan="4" align="right" class="week-total"><strong>TOTAL DUE FOR WEEK {i+1}</strong></td><td class="total"><strong>&pound{weekly_totals[i]:.2f}</strong></td></tr>')
            
            invoice_file.write('\n' + tail_file.read())

# Create PDF invoice
def create_pdf(month=None, year=None, delete_html=True):
    month = month or datetime.datetime.now().month
    year = year or datetime.datetime.now().year
    month_lessons, weekly_totals = group_lessons(month, year)
    create_html(month_lessons, weekly_totals)

    context = {
        'full_name': USER_SETTINGS['full_name'].title(),
        'address': USER_SETTINGS['address'].title(),
        'town': USER_SETTINGS['town'].title(),
        'invoice_date': datetime.datetime.today().strftime("%d %b %Y"),
        'postcode': USER_SETTINGS['postcode'].upper(),
        'invoice_no': f"{year}{month:02}",
        'email': USER_SETTINGS["email"],
        'account_no': USER_SETTINGS["account_no"],
        'sort_code': USER_SETTINGS["sort_code"],
        'monthly_total': f"{sum(weekly_totals):.2f}"
    }

    template_loader = jinja2.FileSystemLoader('./')
    template_env = jinja2.Environment(loader=template_loader)
    template = template_env.get_template(HTML_TEMPLATE_FILE)
    output_text = template.render(context)
    config = pdfkit.configuration(wkhtmltopdf='')

    pdfkit.from_string(output_text, f"invoices/pdf/{year}{month:02}.pdf", configuration=config, css=CSS_FILE)

    if delete_html:
        os.remove(HTML_TEMPLATE_FILE)
    else:
        os.rename(HTML_TEMPLATE_FILE, f"invoices/html/{year}{month:02}.html")