FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt
RUN pip install psycopg2-binary

COPY . .

# Don't steal my tokens pls
ENV OPENAI_API_KEY=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

CMD ["gunicorn", "--worker-class", "eventlet", "--workers", "1", "--bind", "0.0.0.0:5000", "wsgi:app"]