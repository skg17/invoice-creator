import datetime
from quickstart import get_lessons, createPDF

if __name__ == "__main__":
  month_lessons, weekly_total = get_lessons()
  createPDF(month_lessons, weekly_total)