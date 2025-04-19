from flask import Flask, render_template, redirect, url_for, request, flash, send_file
import os
from quickstart import create_pdf, sync_history, fetch_lessons, DB_FILE, Student, init_db
import sqlite3
import json
import datetime

# Filter options for student management
FILTER_YEARS = ['Year 9', 'Year 10', 'Year 11', 'Year 12', 'Year 13']
FILTER_LEVELS = ['GCSE', 'A Level']
FILTER_EXAM_BOARDS = ['AQA', 'Edexcel', 'OCR A', 'OCR B', 'iGCSE']
FILTER_ACTIVE = [(1, 'Current'), (0, 'Past')]

app = Flask(__name__, template_folder='templates')
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key')
DASHBOARD = 'index.html'
STUDENTS_HTML = 'students.html'

@app.route("/", methods=["GET"])
def index():
    # Ensure database and tables are initialized
    init_db()
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
    # Compute earnings per month for each available year
    earnings_data = {}
    for year in available_years:
        monthly_totals = []
        for month in range(1, 13):
            lessons = fetch_lessons(month, year)
            total = sum(lesson.earned for lesson in lessons)
            monthly_totals.append(total)
        earnings_data[year] = monthly_totals

    # Fetch next 5 upcoming lessons with student profiles
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    today_str = now.date().isoformat()
    c.execute(
        """
        SELECT l.date, l.start_time, l.end_time,
               s.id, s.name, s.level, s.year, s.exam_board, s.target_grade, s.subject, s.active
        FROM lessons l
        JOIN students s ON l.student_id = s.id
        WHERE l.date >= ?
        ORDER BY l.date ASC
        LIMIT 5
        """,
        (today_str,)
    )
    rows = c.fetchall()
    conn.close()

    upcoming_lessons = []
    today = now.date()
    for (date_str, start_str, end_str,
         sid, name, level, student_year, exam_board, target_grade, subject, active) in rows:
        # parse lesson date
        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        if date_obj == today:
            relative = "Today"
        elif date_obj == today + datetime.timedelta(days=1):
            relative = "Tomorrow"
        else:
            relative = date_obj.strftime("%A")
        actual = date_obj.strftime("%d %b %Y")
        # parse times
        start_time = datetime.datetime.fromisoformat(start_str).strftime("%H:%M")
        end_time = datetime.datetime.fromisoformat(end_str).strftime("%H:%M")
        # build student object
        student = Student(sid, name, level, student_year, exam_board, target_grade, subject, active)
        upcoming_lessons.append({
            "relative": relative,
            "actual": actual,
            "start_time": start_time,
            "end_time": end_time,
            "student": student
        })

    # Compute statistics
    # Year-to-date earnings for current year
    ytd_total = sum(earnings_data.get(current_year, []))
    # Month-to-date earnings
    mtd_total = earnings_data.get(current_year, [0] * 12)[now.month - 1]
    # Total earnings since the beginning
    conn2 = sqlite3.connect(DB_FILE)
    c2 = conn2.cursor()
    c2.execute("SELECT SUM(duration * hourly_rate) FROM lessons")
    total_all = c2.fetchone()[0] or 0
    conn2.close()

    # Pass data to template
    earnings_data_json = json.dumps(earnings_data)
    return render_template(
        DASHBOARD,
        earnings_data_json=earnings_data_json,
        available_years=available_years,
        selected_years=selected_years,
        upcoming_lessons=upcoming_lessons,
        ytd_total=ytd_total,
        mtd_total=mtd_total,
        total_all=total_all,
        current_month=now.month,
        current_year=current_year
    )

@app.route("/create-invoice")
def create_invoice():
    # Generate PDF and return as download
    pdf_path = create_pdf()
    return send_file(
        pdf_path,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=os.path.basename(pdf_path)
    )

@app.route("/sync-all")
def sync_all():
    sync_history()
    flash("All lessons have been synced successfully.")
    return redirect(url_for("index"))

@app.route("/create-invoice/<int:year>/<int:month>")
def create_invoice_custom(year: int, month: int):
    # Generate custom PDF and return as download
    pdf_path = create_pdf(month, year)
    return send_file(
        pdf_path,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=os.path.basename(pdf_path)
    )

@app.route("/students", methods=["GET", "POST"])
def manage_students():
    """View and edit student properties."""
    # Ensure database structure is set up
    init_db()
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    if request.method == "POST":
        # Handle deletion of a student and their lessons
        delete_id = request.form.get("delete")
        if delete_id:
            c.execute("DELETE FROM lessons WHERE student_id = ?", (delete_id,))
            c.execute("DELETE FROM student_subjects WHERE student_id = ?", (delete_id,))
            c.execute("DELETE FROM students WHERE id = ?", (delete_id,))
            conn.commit()
            conn.close()
            flash("Student and associated lessons deleted.")
            return redirect(url_for("manage_students"))

        # Batch update all students
        student_ids = request.form.getlist("student_ids")
        for sid in student_ids:
            level = request.form.get(f"level-{sid}")
            year_val = request.form.get(f"year-{sid}")
            exam_board = request.form.get(f"exam_board-{sid}")
            target_grade = request.form.get(f"target_grade-{sid}")
            subject_val = request.form.get(f"subject-{sid}")
            active_val = int(request.form.get(f"active-{sid}", 0))
            c.execute("""
                UPDATE students
                SET level=?, year=?, exam_board=?, target_grade=?, subject=?, active=?
                WHERE id=?
            """, (level, year_val, exam_board, target_grade, subject_val, active_val, sid))
        conn.commit()
        conn.close()
        flash("Students updated successfully.")
        return redirect(url_for("manage_students"))

    # GET: fetch all students with optional filters
    year_filter = request.args.get('year')
    level_filter = request.args.get('level')
    board_filter = request.args.get('exam_board')
    active_param = request.args.get('active')
    query = """
        SELECT id, name, level, year, exam_board, target_grade, subject, active
        FROM students
    """
    filters = []
    args = []
    # Default to current students if no active filter provided
    if active_param is None:
        filters.append("active = ?")
        args.append(1)
    else:
        filters.append("active = ?")
        args.append(int(active_param))
    if year_filter:
        filters.append("year = ?")
        args.append(year_filter)
    if level_filter:
        filters.append("level = ?")
        args.append(level_filter)
    if board_filter:
        filters.append("exam_board = ?")
        args.append(board_filter)
    if filters:
        query += " WHERE " + " AND ".join(filters)

    c.execute(query, tuple(args))
    rows = c.fetchall()
    conn.close()

    # Convert to Student objects
    students = [Student.from_db(row) for row in rows]

    return render_template(
        STUDENTS_HTML,
        students=students,
        filter_years=FILTER_YEARS,
        filter_levels=FILTER_LEVELS,
        filter_boards=FILTER_EXAM_BOARDS,
        filter_active=FILTER_ACTIVE
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)