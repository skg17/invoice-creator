from flask import Flask, render_template, redirect, url_for, request, flash
from quickstart import create_pdf, sync_history
import datetime

app = Flask(__name__, template_folder='templates')
app.secret_key = 'supersecretkey'
TEMPLATE = 'index.html'

@app.route("/")
def index():
    return render_template(TEMPLATE)

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