#from docx import Document
import pandas as pd

class Session:
    def __init__(self, day, date, pupil, hrs):
        self.day = day
        self.date = date
        self.pupil = pupil
        self.hrs = hrs

    def __str__(self):
        return 'Session(' + self.day + ':' + self.date + '-' + self.pupil + '[' + str(self.hrs) + ']' + ')'
    
    def __repr__(self):
        return 'Session(' + self.day + ':' + self.date + '-' + self.pupil + '[' + str(self.hrs) + ']' + ')'

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

            sessions[i] = Session(days[i], dates[i], pupil, 1)

            i += 1

        else:
            n_pupils = pupil.count(',')

            for n in range(n_pupils):
                pupil1, pupil2 = pupil.split(',', 1)

                sessions[i] = Session(days[i], dates[i], pupil1, 1)

                pupil = pupil2

            i += 1

    for j in range(len(sessions)):
        if sessions[j].pupil.isalpha() != True:
            pupil, hrs = sessions[j].pupil.split('(')
            hrs = int(hrs.replace(')', ''))

            sessions[j].pupil = pupil
            sessions[j].hrs = hrs

    return sessions