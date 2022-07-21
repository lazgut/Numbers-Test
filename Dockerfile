FROM python:3.9

WORKDIR usr/src/app/

COPY . /usr/src/app/

RUN python -m venv venv

RUN . ./venv/bin/activate

RUN pip install --user httplib2 google-api-python-client oauth2client pandas xmltodict sqlalchemy psycopg2

CMD ["python", "main.py"]
