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
            day[3] = "&pound{}".format(day[3])

        print("\nWeek {}".format(month_lessons.index(week)+1))
        print(tabulate(week, headers=headers, tablefmt='grid'))

        df = pd.DataFrame(week, columns=headers)
        
        weekly_total.append(week_total)
        print("Total earned in Week {0}: &pound{1}".format(month_lessons.index(week)+1, week_total))

        with open('invoice.md', 'a') as f:
            f.write('\n### Week {0} - Total earned: &pound{1}\n'.format(month_lessons.index(week)+1, week_total))
            df.to_markdown(f, index=False)
            f.write('\n\n')      

    print("\nTotal earned in {0} {1}: &pound{2}".format(calendar.month_name[month], year, sum(weekly_total)))

    with open('invoice.md', 'a') as f:
        f.write('\n### Total earned in {0} {1}: &pound{2}'.format(calendar.month_name[month], year, sum(weekly_total)))

    return month_lessons, weekly_total

def createPDF(month_lessons, weekly_total):
    i = 0

    head = open('head.html', 'r')
    tail = open('tail.html', 'r')

    with open('invoice.html', 'a') as f:
        f.write(head.read())
        
        for week in month_lessons:
            for day in week:
                f.write('\n<tr>')
                f.write('\n<td>{}</td>'.format(day[0]))
                f.write('\n<td>{}</td>'.format(day[1]))
                f.write('<td>&pound20</td>')
                f.write('\n<td>{}</td>'.format(day[2]))
                f.write('\n<td class="bold">{}</td>'.format(day[3]))
                f.write('\n</tr>')

            f.write('\n<tr>')
            f.write('\n<td colspan="4" align="right"><strong>Total Earned for Week {}</strong></td>'.format(i+1))
            f.write('\n<td><strong>&pound{}</strong></td>'.format(weekly_total[i]))
            f.write('\n</tr>')
            i += 1

        f.write(tail.read())

    today_date = datetime.datetime.today().strftime("%d %b, %Y")
    invoice_no = 696969
    account_no = 123456
    sort_code = "12-34-56"

    context = {'client_name': 'client_name', 'address_line1': 'address_line1',
               'address_line2': 'address_line2', 'invoice_date': today_date,
               'address_line3': 'address_line3', 'invoice_no': invoice_no,
               'user_email': 'email', 'account_no': account_no, 'sort_code': sort_code,
               'monthly_total': sum(weekly_total)
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