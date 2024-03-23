import datetime
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

    headers = ["Date", "Student", "Hrs", "Earned"]
    print(tabulate(lessons_info, headers=headers, tablefmt='grid'))

if __name__ == "__main__":
  main()