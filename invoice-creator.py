import datetime
import calendar
import jinja2
import pdfkit
import pandas as pd
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
    month_lessons = []

    for i in range(len(lessons_info)):
        week.append(lessons_info[i])
        if (i != len(lessons_info)-1) and (lessons_info[i][4] > lessons_info[i+1][4]):
            #print(lessons_info[i])
            #week += 1
            #print(week)
            month_lessons.append(week)
            week = []
        
        elif i == len(lessons_info)-1:
            month_lessons.append(week)

    weekly_total = []

    for week in month_lessons:
        week_total = 0
        
        for day in week:
            week_total += day[3]
            day[3] = "£{}".format(day[3])

        print("\nWeek {}".format(month_lessons.index(week)+1))
        print(tabulate(week, headers=headers, tablefmt='grid'))

        df = pd.DataFrame(week, columns=headers)
        
        weekly_total.append(week_total)
        print("Total earned in Week {0}: £{1}".format(month_lessons.index(week)+1, week_total))

        with open('invoice.md', 'a') as f:
            f.write('\n### Week {0} - Total earned: £{1}\n'.format(month_lessons.index(week)+1, week_total))
            df.to_markdown(f, index=False)
            f.write('\n\n')      

    print("\nTotal earned in {0} {1}: £{2}".format(calendar.month_name[month], year, sum(weekly_total)))

    with open('invoice.md', 'a') as f:
        f.write('\n### Total earned in {0} {1}: £{2}'.format(calendar.month_name[month], year, sum(weekly_total)))

    return month_lessons, weekly_total

def createPDF(month_lessons, weekly_total):
    i = 0

    with open('invoice.html', 'a') as f, open('head.html', 'r') as head, open('tail.html', 'r') as tail:
        f.write(head.read())

        for week in month_lessons:
            for day in week:
                f.write('\n<tr>')
                f.write('\n<td>{}</td>'.format(day[0]))
                f.write('\n<td>{}</td>'.format(day[1]))
                f.write('\n<td>{}</td>'.format(day[2]))
                f.write('<td>£20</td>')
                f.write('\n<td>{}</td>'.format(day[3]))
                f.write('\n</tr>')

            f.write('\n<tr>')
            f.write('\n<td colspan="4" align="right"><strong>Total Earned for Week {}</strong></td>'.format(i+1))
            f.write('\n<td><strong>£{}</strong></td>'.format(weekly_total[i]))
            f.write('\n</tr>')
            i += 1
        
        f.write(tail.read())

if __name__ == "__main__":
  month_lessons, weekly_total = main()
  createPDF(month_lessons, weekly_total)