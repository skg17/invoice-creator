FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y wkhtmltopdf && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p invoices/pdf invoices/html

EXPOSE 5001

ENV FLASK_APP=server.py
ENV FLASK_ENV=production

CMD ["flask", "run", "--host=0.0.0.0", "--port=5001"]