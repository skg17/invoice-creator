from flask import Flask, render_template, redirect, url_for, request, flash
from quickstart import create_pdf, sync_history, fetch_lessons, DB_FILE
import sqlite3
import json
import datetime

app = Flask(__name__, template_folder='templates')
app.secret_key = 'supersecretkey'
TEMPLATE = 'index.html'

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
    # Pass data to template
    earnings_data_json = json.dumps(earnings_data)
    return render_template(
        TEMPLATE,
        earnings_data_json=earnings_data_json,
        available_years=available_years,
        selected_years=selected_years
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)