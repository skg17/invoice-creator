# Google Calendar Invoice Creator
***Quickly create simple, sleek invoices based on Google Calendar events***

## About the Project
As a private tutor, the worst part of the month is having to write an invoice meticulously logging all the lessons taught, including dates, students, durations...
This program fixes that, by creating an invoice in PDF format using event information from your Google Calendar!

Here's how it works:
1. An API call is made to get all events from your calendar.
2. The month is broken down into weeks, and the amount earned is tracked for every hour, session, week and month.
3. An HTML template for the invoice is created using a modified version of the [Anvil HTML Invoice Template](https://github.com/anvilco/html-pdf-invoice-template).
4. The template is then converted to a PDF using Jinja2.


## Getting Started

### Prerequisites
- Python 3.7 or higher (developed using Python 3.11)
- Google Calendar API credentials

### Installation
1. **Clone this repository:**
    ```bash
    git clone https://github.com/skg17/invoice-creator.git
    cd invoice-creator
    ```
2. **Create and activate a virtual environment:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```
3. **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4. **Set up the Google Calendar API:**
    - Follow the [Google Calendar API Python Quickstart](https://developers.google.com/calendar/api/quickstart/python) to obtain `credentials.json`.
    - Move `credentials.json` to the `src/calendar_display` sub-directory.

### Project Structure
At this point, the folder structure should look like this:
```arduino
invoice-creator/
├── src/
│   └── invoice_creator/
│       ├── invoice/
│       │   ├── html/
│       │   └── pdf/
│       ├── templates/
│       │   ├── head.html
│       │   ├── new_table.html
│       │   └── tail.html
│       ├── static/
│       │   └── css/
│       │       └── invoice_styles.css
│       ├── credentials.json
│       ├── main.py
│       └── quickstart.py
├── LICENSE
├── README.md
└── requirements.txt
```

### First Run
1. **Navigate to the app directory:**
    ```bash
        cd app/invoice_creator
    ```
2. **Run the script:**
    ```bash
        python main.py
    ```

3. **Complete the required setup:**
    1. **Enter the required information to set up `user_settings.json` when prompted:**
        - **Address:** the first line of your address (house number and street name).
        - **Control str:** this refers to a 'control string', a string which will be stripped from the event name and will be assumed to precede the student name. This for example could be something like "Tutoring with", in which case the program will look for any event names with the substring "Tutoring with" and use the subsequent word as the student name.
        - **Hourly rate:** the hourly rate charged per lesson. This has to be input as an integer, without any preceding currency symbols.
        - **Account no:** the bank account number to which the money is to be sent.
        - **Sort code:** the sort code corresponding to the bank account.

    2. **Complete the Google Calendar authorisation:**
        When prompted to do so, log into the Google account corresponding to the calendar.


## Contributing
Contributions are welcome! Please submit a pull request or open an issue to discuss any changes.

## License
This project is licensed under the MIT License. See the [LICENSE](https://github.com/skg17/invoice-creator/blob/main/LICENSE) file for details.

## Acknowledgements
Thanks to Anvil for making the [HTML template](https://github.com/anvilco/html-pdf-invoice-template) available!
