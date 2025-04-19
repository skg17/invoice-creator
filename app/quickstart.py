import datetime
import os
import sqlite3
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
DB_FILE = "lessons.db"
HTML_TEMPLATE_FILE = 'invoices/html/invoice.html'
CSS_FILE = 'static/css/invoice_styles.css'
HEAD_TEMPLATE = 'templates/head.html'
TAIL_TEMPLATE = 'templates/tail.html'
NEW_TABLE_TEMPLATE = 'templates/new_table.html'
USER_SETTINGS = get_user_settings()

def get_student_name(control_str: str, event: dict) -> str:
    """Extracts the student name by stripping the control string from the event summary."""
    stripped_str = event["summary"].replace(control_str, "").strip()
    student, *_ = stripped_str.split(" ")
    return student

def get_lesson_date(event: dict) -> datetime.date:
    """Fetches the lesson date from the event start time."""
    return datetime.datetime.fromisoformat(
        event["start"].get("dateTime", event["start"].get("date"))
    ).date()

def get_duration(event: dict) -> float:
    """Calculates lesson duration in hours from event start and end times."""
    start = datetime.datetime.fromisoformat(
        event["start"].get("dateTime", event["start"].get("date"))
    )
    end = datetime.datetime.fromisoformat(
        event["end"].get("dateTime", event["end"].get("date"))
    )
    return (end - start).total_seconds() / 3600

# Initialize SQLite database and lessons table
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS lessons (
            event_id TEXT PRIMARY KEY,
            date TEXT NOT NULL,
            weekday INTEGER NOT NULL,
            student TEXT NOT NULL,
            duration REAL NOT NULL,
            hourly_rate REAL NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

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

# Sync Google Calendar events into the SQLite database
def sync_calendar(month: int, year: int) -> None:
    init_db()
    creds = get_google_credentials()
    try:
        service = build("calendar", "v3", credentials=creds)
        time_min = datetime.datetime(year, month, 1).isoformat() + "Z"
        next_month = month + 1 if month < 12 else 1
        next_year = year + 1 if month == 12 else year
        time_max = datetime.datetime(next_year, next_month, 1).isoformat() + "Z"

        events_result = service.events().list(
            calendarId="primary", timeMin=time_min, timeMax=time_max,
            maxResults=1000, singleEvents=True, orderBy="startTime"
        ).execute()
        events = events_result.get("items", [])

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        for event in events:
            event_id = event["id"]
            date_obj = datetime.datetime.fromisoformat(
                event["start"].get("dateTime", event["start"].get("date"))
            ).date()
            date_str = date_obj.strftime("%Y-%m-%d")
            weekday = date_obj.weekday()
            student = get_student_name(USER_SETTINGS["control_str"], event)
            duration = get_duration(event)
            hourly_rate = float(USER_SETTINGS["hourly_rate"])
            c.execute('''
                INSERT OR REPLACE INTO lessons (
                    event_id, date, weekday, student, duration, hourly_rate
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (event_id, date_str, weekday, student, duration, hourly_rate))
        conn.commit()
        conn.close()
    except HttpError as error:
        print(f"An error occurred: {error}")

def sync_history(end_month: int = None,
                 end_year: int = None,
                 start_month: int = None,
                 start_year: int = None,
                 years_back: int = 5) -> None:
    """Syncs Google Calendar events from a past start date up through an end date.
    By default, syncs the last `years_back` years ending at the given month/year (or today)."""
    # Determine end date
    if end_month is None or end_year is None:
        now = datetime.datetime.now()
        end_month, end_year = now.month, now.year

    # Determine start date (default years_back ago)
    if start_month is None or start_year is None:
        start_year = end_year - years_back
        start_month = end_month

    cur_year, cur_month = start_year, start_month
    # Loop month-by-month until end date inclusive
    while (cur_year < end_year) or (cur_year == end_year and cur_month <= end_month):
        sync_calendar(cur_month, cur_year)
        # advance one month
        if cur_month == 12:
            cur_month = 1
            cur_year += 1
        else:
            cur_month += 1

# Fetch lessons from the database for a given month/year
def fetch_lessons(month: int, year: int):
    init_db()
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    start_date = datetime.date(year, month, 1)
    if month == 12:
        end_date = datetime.date(year + 1, 1, 1)
    else:
        end_date = datetime.date(year, month + 1, 1)
    c.execute('''
        SELECT date, weekday, student, duration, hourly_rate
        FROM lessons
        WHERE date >= ? AND date < ?
        ORDER BY date
    ''', (start_date.isoformat(), end_date.isoformat()))
    rows = c.fetchall()
    conn.close()

    lessons = []
    for date_str, weekday, student, duration, hourly_rate in rows:
        lesson = Lesson.from_db(date_str, weekday, student, duration, hourly_rate)
        lessons.append(lesson)
    return lessons

# Type aliases
type Date = datetime.date
type LessonList = list["Lesson"]

class Lesson:
    """Class containing information relating to a lesson."""
    def __init__(self, event) -> None:
        self.date = get_lesson_date(event).strftime('%d/%m/%Y')
        self.weekday = get_lesson_date(event).weekday()
        self.student = get_student_name(USER_SETTINGS["control_str"], event)
        self.duration = get_duration(event)
        self.hourly_rate = float(USER_SETTINGS["hourly_rate"])
        self.earned = self.duration * self.hourly_rate

    @classmethod
    def from_db(cls, date_str, weekday, student, duration, hourly_rate):
        obj = cls.__new__(cls)
        obj.date = datetime.datetime.strptime(date_str, '%Y-%m-%d').strftime('%d/%m/%Y')
        obj.weekday = weekday
        obj.student = student
        obj.duration = duration
        obj.hourly_rate = hourly_rate
        obj.earned = duration * hourly_rate
        return obj

    def __repr__(self) -> str:
        return f'{self.date}: {self.student}, {self.earned:.2f} ({self.duration}h @ {self.hourly_rate}/hr)'

    def add_currency_symbol(self, currency: str = '&pound') -> None:
        self.earned = f"{currency}{self.earned:.2f}"

def sorting_logic(lesson: Lesson):
    return datetime.datetime.strptime(lesson.date, '%d/%m/%Y').date()

def group_lessons(month: int, year: int) -> tuple[list[LessonList], list[float]]:
    """Returns lessons grouped by week and total earnings per week."""
    # Sync latest events then fetch from DB
    sync_calendar(month, year)
    lessons_info = fetch_lessons(month, year)

    lessons_info.sort(key=sorting_logic)
    month_lessons: list[LessonList] = []
    week: LessonList = []

    for i, lesson in enumerate(lessons_info):
        week.append(lesson)
        next_day_jump = (
            i == len(lessons_info) - 1 or
            lesson.weekday > lessons_info[i + 1].weekday or
            (int(lessons_info[i + 1].date.split('/')[0]) >= int(lesson.date.split('/')[0]) + 7)
        )
        if next_day_jump:
            month_lessons.append(week)
            week = []

    weekly_totals = [sum(l.duration * l.hourly_rate for l in w) for w in month_lessons]
    for week in month_lessons:
        for lesson in week:
            lesson.add_currency_symbol()
    return month_lessons, weekly_totals

def create_html(month_lessons: list[LessonList], weekly_totals: list[float]) -> None:
    """Creates an HTML invoice using pre-set templates."""
    hourly_rate = USER_SETTINGS["hourly_rate"]
    with open(HEAD_TEMPLATE) as head, \
         open(TAIL_TEMPLATE) as tail, \
         open(NEW_TABLE_TEMPLATE) as table, \
         open(HTML_TEMPLATE_FILE, 'w') as out:
        out.write(head.read())
        rows = table.read()
        for i, week in enumerate(month_lessons):
            out.write(rows)
            for lesson in week:
                out.write(f"<tr><td>{lesson.date}</td><td>{lesson.student}</td>"
                          f"<td>&pound{hourly_rate:.2f}</td><td>{lesson.duration}</td>"
                          f"<td class='bold'>{lesson.earned}</td></tr>")
            out.write(f"<tr><td colspan='4' align='right' class='week-total'>"
                      f"<strong>TOTAL DUE FOR WEEK {i+1}</strong></td>"
                      f"<td class='total'><strong>&pound{weekly_totals[i]:.2f}</strong></td></tr>")
        out.write(tail.read())

def create_pdf(month: int = None, year: int = None, delete_html: bool = True) -> None:
    if month is None or year is None:
        now = datetime.datetime.now()
        month, year = now.month, now.year
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
    loader = jinja2.FileSystemLoader('./')
    env = jinja2.Environment(loader=loader)
    template = env.get_template(HTML_TEMPLATE_FILE)
    output_text = template.render(context)
    config = pdfkit.configuration(wkhtmltopdf='')
    pdfkit.from_string(output_text, f"invoices/pdf/{year}{month:02}.pdf", configuration=config, css=CSS_FILE)
    if delete_html:
        os.remove(HTML_TEMPLATE_FILE)
    else:
        os.rename(HTML_TEMPLATE_FILE, f"invoices/html/{year}{month:02}.html")