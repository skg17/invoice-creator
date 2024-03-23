import datetime
import calendar
from tabulate import tabulate
from quickstart import get_lessons_info

def main():
    month = datetime.datetime.now().month
    year = datetime.datetime.now().year

    control_str = "Mr Sahil with "
    hourly_rate = 20

    lessons_info = get_lessons_info(month, year, control_str)

    for i in range(len(lessons_info)):
        lessons_info[i].append(hourly_rate * lessons_info[i][2])
        lessons_info[i].append(lessons_info[i][0].weekday())
        lessons_info[i][0] = lessons_info[i][0].strftime('%d/%m/%Y')

    lessons_info.sort()

    headers = ["Date", "Student", "Hrs", "Earned", "Weekday"]
    #print(tabulate(lessons_info, headers=headers, tablefmt='grid'))

    week = []
    month = []

    for i in range(len(lessons_info)):
        week.append(lessons_info[i])
        if (i != len(lessons_info)-1) and (lessons_info[i][4] > lessons_info[i+1][4]):
            #print(lessons_info[i])
            #week += 1
            #print(week)
            month.append(week)
            week = []
        
        elif i == len(lessons_info)-1:
            month.append(week)

    for week in month:
        print(tabulate(week, headers=headers, tablefmt='grid'))

if __name__ == "__main__":
  main()