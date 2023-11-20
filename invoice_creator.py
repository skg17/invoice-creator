from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL
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

def sessions_creator(df):
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

def week_sort(sessions):
    weeks = {}
    week = []
    j = 0

    for i in range(len(sessions)):
        week.append(sessions[i])

        if sessions[i].day == 'Sunday':
            weeks[j] = week
            week = []
            j += 1

    weeks[j] = week

    return weeks

def create_invoice(sessions, weeks):
    day, month, year = sessions[0].date.split('/')
    month_name = calendar.month_name[int(month)]

    month_total = 0
    for i in range(len(sessions)):
        month_total += sessions[i].earned

    doc = Document()
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Arial'
    font.size = Pt(10)

    n_rows = len(sessions)+len(weeks)+1
    t = doc.add_table(rows=n_rows, cols=5)
    t.style = 'Table Grid'

    i = 0

    for j in range(len(weeks)):
        a = t.cell(i, 0)
        b = t.cell(i, 1)
        c = t.cell(i, 2)
        d = t.cell(i, 3)
        e = t.cell(i, 4)

        A = a.merge(b)
        B = A.merge(c)
        C = B.merge(d)
        D = C.merge(e)

        D = D.add_paragraph("Week {}".format(j+1))
        D.alignment = WD_ALIGN_PARAGRAPH.CENTER

        i += 1

        week_total = 0

        for session in weeks[j]:
            t.cell(i, 0).text = str(session.date)
            t.cell(i, 1).text = str(session.pupil)
            t.cell(i, 2).text = str(session.hrs)
            t.cell(i, 3).text = '£' + str(session.earned)

            week_total += session.earned

            i += 1

        for k in range(len(weeks[j])):
            a = t.cell(i-1, 4)
            b = t.cell(i-1-k, 4)

            A = a.merge(b)

    a = t.cell(n_rows-1, 0)
    b = t.cell(n_rows-1, 1)
    c = t.cell(n_rows-1, 2)
    d = t.cell(n_rows-1, 3)
    t.cell(n_rows-1, 4).text = '£' + str(month_total)
    t.cell(n_rows-1, 4).vertical_alignment = WD_ALIGN_VERTICAL.BOTTOM

    A = a.merge(b)
    B = A.merge(c)
    C = B.merge(d)
    C = C.add_paragraph('Total for ' + month_name + ' ' + str(year))
    C.alignment = WD_ALIGN_PARAGRAPH.RIGHT

    doc.save('{0}_invoice.docx'.format(month_name))

    