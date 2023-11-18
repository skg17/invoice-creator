from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
import pandas as pd
import calendar

class Session:
    def __init__(self, day, date, pupil, hrs, earned):
        self.day = day
        self.date = date
        self.pupil = pupil
        self.hrs = hrs
        self.earned = earned

    def __str__(self):
        return 'Session(' + self.day[:3] + ', ' + self.date + ' - ' + self.pupil + '(' + str(self.hrs) + ') - £' + str(self.earned) + ')'
    
    def __repr__(self):
        return 'Session(' + self.day[:3] + ', ' + self.date + ' - ' + self.pupil + '(' + str(self.hrs) + ') - £' + str(self.earned) + ')'

def read_log(filepath):
    df = pd.read_csv(filepath)
    df = df[['Day', 'Date', 'Pupils']]

    df = df.loc[df['Pupils'].notnull(), ['Day', 'Date', 'Pupils']]
    
    return df

def split_days(df):
    pupils = []
    days = [i for i in df['Day']]
    dates = [i for i in df['Date']]

    i = 0
    j = 0

    sessions = {}

    for pupil in df['Pupils']:
        if pupil.isalpha() == True:
            pupils.append(pupil)

            sessions[j] = Session(days[i], dates[i], pupil, 1, 20)
            j += 1
            i += 1

        else:
            n_pupils = pupil.count(',')

            for n in range(n_pupils):
                pupil1, pupil2 = pupil.split(',', 1)

                sessions[j] = Session(days[i], dates[i], pupil1, 1, 20)
                j += 1

                pupil = pupil2

            sessions[j] = Session(days[i], dates[i], pupil, 1, 20)
            j += 1
            i += 1

    for j in range(len(sessions)):
        if sessions[j].pupil.isalpha() != True:
            pupil, hrs = sessions[j].pupil.split('(')
            hrs = int(hrs.replace(')', ''))

            sessions[j].pupil = pupil
            sessions[j].hrs = hrs
            sessions[j].earned = hrs * 20

    return sessions

def create_invoice(sessions):
    month_total = 0
    day, month, year = sessions[0].date.split('/')
    month_name = calendar.month_name[int(month)]

    for i in range(len(sessions)):
        month_total += sessions[i].earned

    doc = Document()
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Arial'
    font.size = Pt(10)

    n_weeks = (len(sessions) // 7) + 1

    t = doc.add_table(rows=len(sessions)+n_weeks+1, cols=5)
    t.style = 'Table Grid'

    weeks = {}
    week = []

    for i in range(len(sessions)):
        week.append(sessions[i])

        if sessions[i].day == 'Sunday':
            weeks[i] = week
            week = []

    return weeks

    