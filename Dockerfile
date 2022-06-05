FROM python:3.10.4-buster

COPY app app
COPY requirements.txt requirements.txt
COPY csgo csgo

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

CMD uvicorn app.api:app --host 0.0.0.0 --port $PORT
