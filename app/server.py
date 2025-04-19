from flask import Flask, render_template, redirect, url_for, request, flash
from quickstart import create_pdf, sync_history, fetch_lessons, DB_FILE
import sqlite3
import json
import datetime

app = Flask(__name__, template_folder='templates')
app.secret_key = 'supersecretkey'
DASHBOARD = 'index.html'
STUDENTS_HTML = 'students.html'

@app.route("/", methods=["GET"])
def index():
    # Determine current year
    now = datetime.datetime.now()
    current_year = now.year
    # Get selected years from query parameters
    selected_years = request.args.getlist('year', type=int)
    if not selected_years:
        selected_years = [current_year]
    # Determine earliest recorded lesson year
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT MIN(date) FROM lessons")
    min_date = c.fetchone()[0]
    conn.close()
    min_year = int(min_date.split("-")[0]) if min_date else current_year
    available_years = list(range(min_year, current_year + 1))
    # Compute earnings per month for each selected year
    earnings_data = {}
    for year in selected_years:
        monthly_totals = []
        for month in range(1, 13):
            lessons = fetch_lessons(month, year)
            total = sum(lesson.earned for lesson in lessons)
            monthly_totals.append(total)
        earnings_data[year] = monthly_totals

    # Fetch next 5 upcoming lessons
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    today_str = now.date().isoformat()
    c.execute(
        "SELECT date, student, start_time, end_time FROM lessons "
        "WHERE date >= ? ORDER BY date ASC LIMIT 5",
        (today_str,)
    )
    rows = c.fetchall()
    conn.close()

    upcoming_lessons = []
    today = now.date()
    for date_str, student, start_str, end_str in rows:
        # parse lesson date
        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        # determine relative label
        if date_obj == today:
            relative = "Today"
        elif date_obj == today + datetime.timedelta(days=1):
            relative = "Tomorrow"
        else:
            relative = date_obj.strftime("%A")
        actual = date_obj.strftime("%d %b %Y")
        # parse start/end times
        start_dt = datetime.datetime.fromisoformat(start_str)
        end_dt = datetime.datetime.fromisoformat(end_str)
        start_time = start_dt.strftime("%H:%M")
        end_time = end_dt.strftime("%H:%M")
        upcoming_lessons.append({
            "relative": relative,
            "actual": actual,
            "start_time": start_time,
            "end_time": end_time,
            "student": student
        })

    # Pass data to template
    earnings_data_json = json.dumps(earnings_data)
    return render_template(
        DASHBOARD,
        earnings_data_json=earnings_data_json,
        available_years=available_years,
        selected_years=selected_years,
        upcoming_lessons=upcoming_lessons
    )

@app.route("/create-invoice")
def create_invoice():
    create_pdf()
    flash("Invoice for the current month has been created successfully.")
    return redirect(url_for("index"))

@app.route("/sync-all")
def sync_all():
    sync_history()
    flash("All lessons have been synced successfully.")
    return redirect(url_for("index"))

@app.route("/create-invoice/<int:year>/<int:month>")
def create_invoice_custom(year: int, month: int):
    create_pdf(month, year)
    flash(f"Invoice for {year}-{month:02} has been created successfully.")
    return redirect(url_for("index"))

@app.route("/students", methods=["GET", "POST"])
def manage_students():
    """View and edit student properties."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    if request.method == "POST":
        student_id = int(request.form["id"])
        level = request.form.get("level")
        year = request.form.get("year")
        exam_board = request.form.get("exam_board")
        target_grade = request.form.get("target_grade")
        subject = request.form.get("subject")
        active = 1 if request.form.get("active") == "on" else 0
        c.execute("""
            UPDATE students
            SET level=?, year=?, exam_board=?, target_grade=?, subject=?, active=?
            WHERE id=?
        """, (level, year, exam_board, target_grade, subject, active, student_id))
        conn.commit()
        flash("Student updated successfully.")
        return redirect(url_for("manage_students"))
    # GET: fetch all students
    c.execute("""
        SELECT id, name, level, year, exam_board, target_grade, subject, active
        FROM students
    """)
    students = c.fetchall()
    conn.close()
    return render_template(STUDENTS_HTML, students=students)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)