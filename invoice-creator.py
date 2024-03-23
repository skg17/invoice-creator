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

    week = 1
    week_day_one = 0

    for i in range(len(lessons_info)):
        if (i != len(lessons_info)-1) and (lessons_info[i][4] > lessons_info[i+1][4]):
            print(tabulate(lessons_info[week_day_one:i+1], tablefmt='grid'))

            week += 1
            week_day_one = i+1
            print(week)

if __name__ == "__main__":
  main()