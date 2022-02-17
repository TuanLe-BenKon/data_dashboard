FROM python:3.8-slim-buster

ENV PYTHONUNBUFFERED 1

COPY ./requirements.txt /requirements.txt
RUN pip3 install -r /requirements.txt

WORKDIR /django
COPY . .

CMD [ "python3", "manage.py", "runserver", "0.0.0.0:8001"]