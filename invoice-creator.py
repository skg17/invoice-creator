import datetime
import calendar
import jinja2
import pdfkit
import json
from tabulate import tabulate
from quickstart import get_lessons_info

def main():
    month = datetime.datetime.now().month
    year = datetime.datetime.now().year

    user_settings = json.load(open('user_settings.json'))

    control_str = user_settings["control_str"]
    hourly_rate = user_settings["hourly_rate"]

    lessons_info = get_lessons_info(month, year, control_str)

    for i in range(len(lessons_info)):
        lessons_info[i].append(hourly_rate * lessons_info[i][2])
        lessons_info[i].append(lessons_info[i][0].weekday())
        lessons_info[i][0] = lessons_info[i][0].strftime('%d/%m/%Y')

    lessons_info.sort()

    headers = ["Date", "Student", "Hrs", "Earned", "Weekday"]

    week = []
    month_lessons = []

    for i in range(len(lessons_info)):
        week.append(lessons_info[i])
        if (i != len(lessons_info)-1) and (lessons_info[i][4] > lessons_info[i+1][4]):
            month_lessons.append(week)
            week = []
        
        elif i == len(lessons_info)-1:
            month_lessons.append(week)

    weekly_total = []

    for week in month_lessons:
        week_total = 0
        
        for day in week:
            week_total += day[3]
            day[3] = "&pound{0:.2f}".format(day[3])

        print("\nWeek {}".format(month_lessons.index(week)+1))
        print(tabulate(week, headers=headers, tablefmt='grid'))
        
        weekly_total.append(week_total)
        print("Total earned in Week {0}: £{1:2f}".format(month_lessons.index(week)+1, week_total))

    print("\nTotal earned in {0} {1}: £{2:.2f}".format(calendar.month_name[month], year, sum(weekly_total)))

    return month_lessons, weekly_total

def createPDF(month_lessons, weekly_total):
    i = 0

    head = open('head.html', 'r')
    tail = open('tail.html', 'r')
    new_table = open('new_table.html', 'r').read()
    user_settings = json.load(open('user_settings.json'))

    with open('invoice.html', 'a') as f:
        f.write(head.read())
        
        for week in month_lessons:
            f.write(new_table)
            for day in week:
                f.write('\n<tr>')
                f.write('\n<td>{}</td>'.format(day[0]))
                f.write('\n<td>{}</td>'.format(day[1]))
                f.write('\n<td>&pound{0:.2f}</td>'.format(user_settings["hourly_rate"]))
                f.write('\n<td>{}</td>'.format(day[2]))
                f.write('\n<td class="bold">{}</td>'.format(day[3]))
                f.write('\n</tr>')

            f.write('\n<tr>')
            f.write('\n<td colspan="4" align="right" class="week-total"><strong>TOTAL DUE FOR WEEK {}</strong></td>'.format(i+1))
            f.write('\n<td class="total"><strong>&pound{0:.2f}</strong></td>'.format(weekly_total[i]))
            f.write('\n')
            i += 1

        f.write('\n')
        f.write(tail.read())

    today_date = datetime.datetime.today().strftime("%d %b, %Y")
    _, month, year = month_lessons[0][0][0].split('/')
    invoice_no = year + month

    context = {'client_name': user_settings['client_name'],
               'address_line1': user_settings['address_line1'],
               'address_line2': user_settings['address_line2'],
               'invoice_date': today_date,
               'address_line3': user_settings['address_line3'],
               'invoice_no': invoice_no,
               'user_email': user_settings["user_email"],
               'account_no': user_settings["account_no"],
               'sort_code': user_settings["sort_code"],
               'monthly_total': "{0:.2f}".format(sum(weekly_total))
    }

    template_loader = jinja2.FileSystemLoader('./')
    template_env = jinja2.Environment(loader=template_loader)

    html_template = 'invoice.html'
    template = template_env.get_template(html_template)
    output_text = template.render(context)

    config = pdfkit.configuration(wkhtmltopdf='')
    output_pdf = 'invoice.pdf'
    pdfkit.from_string(output_text, output_pdf, configuration=config, css='invoice.css')

if __name__ == "__main__":
  month_lessons, weekly_total = main()
  createPDF(month_lessons, weekly_total)