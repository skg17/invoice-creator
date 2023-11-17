from docx import Document
from docx.shared import Pt
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

    sessions = {}

    for pupil in df['Pupils']:
        if pupil.isalpha() == True:
            pupils.append(pupil)

            sessions[i] = Session(days[i], dates[i], pupil, 1, 20)

            i += 1

        else:
            n_pupils = pupil.count(',')

            for n in range(n_pupils):
                pupil1, pupil2 = pupil.split(',', 1)

                sessions[i] = Session(days[i], dates[i], pupil1, 1, 20)

                pupil = pupil2

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

    t = doc.add_table(rows=len(sessions), cols=5)

    for i in range(len(sessions)):
        t.cell(i, 0).text = str(sessions[i].date)
        t.cell(i, 1).text = str(sessions[i].pupil)
        t.cell(i, 2).text = str(sessions[i].hrs)
        t.cell(i, 3).text = '£' + str(sessions[i].earned)

        if sessions[i].day == "Sunday":
            week_total = 0

            if i < 7:
                for j in range(i):
                    week_total += sessions[i-j].earned

            else:
                for j in range(7):
                    week_total += sessions[i-j].earned

            t.cell(i, 4).text = '£' + str(week_total)

    doc.save('{0}_invoice.docx'.format(month_name))