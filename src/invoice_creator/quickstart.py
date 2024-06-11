import datetime
import os
import json
import calendar
import jinja2
import pdfkit
from settings import get_user_settings
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Constants
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"
HTML_TEMPLATE_FILE = 'invoices/html/invoice.html'
CSS_FILE = 'static/css/invoice_styles.css'
HEAD_TEMPLATE = 'templates/head.html'
TAIL_TEMPLATE = 'templates/tail.html'
NEW_TABLE_TEMPLATE = 'templates/new_table.html'
USER_SETTINGS = get_user_settings()

# Type aliases
type Date = datetime.datetime
type LessonList = list[Lesson]

class Lesson:
    """Class containg information relating to a lesson."""
    def __init__(self, event) -> None:
        """Initialises lesson instance.

        :param event: calendar event from which lesson info is to be extracted.
        :type event: dict
        """
        self.date = get_lesson_date(event).strftime('%d/%m/%Y')
        self.weekday = get_lesson_date(event).weekday()
        self.student = get_student_name(USER_SETTINGS["control_str"], event)
        self.duration = get_duration(event)
        self.earned = self.duration * float(USER_SETTINGS["hourly_rate"])

    def add_currency_symbol(self, currency: str = '&pound') -> None:
        """Changes the 'earned' attribute from float to a str preceded by a currency symbol.

        :param currency: currency symbol to be used, defaults to '&pound'
        :type currency: str, optional
        """
        self.earned = f"&pound{self.earned:.2f}"

# Fetch Google credentials
def get_google_credentials() -> Credentials:
    """Fetches Google credentials required to communicate with the Google Calendar API.

    :return: Google credentials.
    :rtype: Credentials
    """
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
def get_lessons_info(month: int, year: int) -> LessonList:
    """Collects info on all the lessons in a given month and year.

    :param month: specify month for which lessons are to be returned.
    :type month: int
    :param year: specify year for which lessons are to be returned.
    :type year: int
    :return: a list containing all the Lesson objects for the given month/year range.
    :rtype: LessonList
    """
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
        
        return [Lesson(event) for event in events]
    
    except HttpError as error:
        print(f"An error occurred: {error}")
        return []

# Group lessons info by weeks
def group_lessons(month: int, year: int) -> tuple[list[LessonList], list[float]]:
    """Returns all the lessons within a given month/year range grouped by week,
    alongside a list of total weekly earnings for said weeks.

    :param month: specify month for which lessons are to be returned.
    :type month: int
    :param year: specify year for which lessons are to be returned.
    :type year: int
    :returns:
        - month_lessons (:py:class:`list[LessonList]`) - all the lessons in the month grouped by week.
        - weekly_totals (:py:class:`list[float]`) - total earnings for each week.
    """
    lessons_info = get_lessons_info(month, year)
    lessons_info.sort(key = sorting_logic)

    week: LessonList = []
    month_lessons: list[LessonList] = []

    for i, lesson in enumerate(lessons_info):
        week.append(lesson)

        if i != len(lessons_info) - 1 and lesson.weekday > lessons_info[i + 1].weekday:
            month_lessons.append(week)
            week = []

        elif i == len(lessons_info) - 1:
            month_lessons.append(week)

    weekly_totals = [sum(lesson.earned for lesson in week) for week in month_lessons]

    for week in month_lessons:
        for lesson in week:
            lesson.add_currency_symbol()

    return month_lessons, weekly_totals

# Get student name from event
def get_student_name(control_str: str, event: str) -> str:
    stripped_str = event["summary"].replace(control_str, "").strip()
    student, *_ = stripped_str.split(" ")

    return student

# Get lesson date
def get_lesson_date(event: dict) -> Date:
    """Fetches lesson date from event dictionary.

    :param event: calendar event from which lesson date is to be extracted.
    :type event: dict
    :return: lesson date.
    :rtype: Date
    """
    return datetime.datetime.fromisoformat(event["start"].get("dateTime", event["start"].get("date"))).date()

# Get lesson duration
def get_duration(event: dict) -> Date:
    """Fetches lesson duration from event dictionary.

    :param event: calendar event from which lesson duration is to be extracted.
    :type event: dict
    :return: lesson duration.
    :rtype: Date
    """
    return (datetime.datetime.fromisoformat(event["end"].get("dateTime", event["end"].get("date"))).time().hour - 
            datetime.datetime.fromisoformat(event["start"].get("dateTime", event["start"].get("date"))).time().hour +
            (datetime.datetime.fromisoformat(event["end"].get("dateTime", event["end"].get("date"))).time().minute -
             datetime.datetime.fromisoformat(event["start"].get("dateTime", event["start"].get("date"))).time().minute) / 60)

# Key for sort function
def sorting_logic(lesson: Lesson) -> Date:
    """Used to specify chronological sorting for `sort()` function. 

    :param lesson: lesson from which date will be extracted.
    :type lesson: Lesson
    :return: lesson date.
    :rtype: Date
    """
    return lesson.date

# Create HTML file for invoice
def create_html(month_lessons: list[LessonList], weekly_totals: list[float]) -> None:
    """Creates an html version of the invoice using pre-set templates.

    :param month_lessons: list of lessons grouped by weeks.
    :type month_lessons: list[LessonList]
    :param weekly_totals: list of total weekly earnings.
    :type weekly_totals: list[float]
    """
    hourly_rate = USER_SETTINGS["hourly_rate"]

    with open(HEAD_TEMPLATE, 'r') as head_file, open(TAIL_TEMPLATE, 'r') as tail_file, open(NEW_TABLE_TEMPLATE, 'r') as table_file:
        with open(HTML_TEMPLATE_FILE, 'w') as invoice_file:
            invoice_file.write(head_file.read())
            table_template = table_file.read()

            for i, week in enumerate(month_lessons):
                invoice_file.write(table_template)

                for lesson in week:
                    invoice_file.write(f'\n<tr><td>{lesson.date}</td><td>{lesson.student}</td><td>&pound{hourly_rate:.2f}</td><td>{lesson.duration}</td><td class="bold">{lesson.earned}</td></tr>')
                invoice_file.write(f'\n<tr><td colspan="4" align="right" class="week-total"><strong>TOTAL DUE FOR WEEK {i+1}</strong></td><td class="total"><strong>&pound{weekly_totals[i]:.2f}</strong></td></tr>')
            
            invoice_file.write('\n' + tail_file.read())

# Create PDF invoice
def create_pdf(month: int = None, year: int = None, delete_html: bool = True) -> None:
    """Creates PDF invoice using html version.

    :param month: month for which invoice is to be created, defaults to None (current month).
    :type month: int, optional
    :param year: year for which invoice is to be created, defaults to None (current year).
    :type year: int, optional
    :param delete_html: toggle whether to delete html invoice, defaults to True (deletes html invoice).
    :type delete_html: bool, optional
    """
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