from .quickstart import create_pdf
import argparse

def main():
  parser = argparse.ArgumentParser(description='Creates an invoice for the specified month/year.')
  parser.add_argument('--month', type=int, help='Enter the invoice month as a number (e.g. March = 3).')
  parser.add_argument('--year', type=int, help='Enter the invoice year (e.g. 2024).')
  parser.add_argument('--html', action='store_false', help='Keeps generated invoice HTML (deleted by default).')
  args = parser.parse_args()

  create_pdf(month=args.month, year=args.year, delete_html=args.html)

if __name__ == "__main__":
  main()