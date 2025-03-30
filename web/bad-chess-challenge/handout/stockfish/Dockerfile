FROM --platform=amd64 python:3.13
WORKDIR /opt
COPY ./stockfish-ubuntu-x86-64-avx2 .
RUN chmod +x stockfish-ubuntu-x86-64-avx2
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY main.py .
CMD ["gunicorn", "--workers=4", "--bind=0.0.0.0:8000", "main:app"]