FROM python:3.8-buster

COPY ./project/requirements.txt /build/

COPY ./confs/uwsgi.ini /build/

COPY ./entrypoint.sh .

RUN chmod +x /entrypoint.sh

RUN pip install --upgrade pip

RUN pip install -r /build/requirements.txt

WORKDIR /app
