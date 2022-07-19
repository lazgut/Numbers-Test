FROM python:3.9

WORKDIR usr/src/app/

COPY . /usr/src/app/

RUN python -m venv venv

RUN . ./venv/bin/activate

RUN pip install --user [libs]

CMD ["python", "run.py"]