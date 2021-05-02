FROM python:3.6-buster

WORKDIR /app

COPY project/requirements.txt /app/
COPY project/uwsgi.ini /app/
COPY entrypoint.sh /

RUN chmod +x /entrypoint.sh
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

RUN mkdir /logs
