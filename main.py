from pprint import pprint

from time import sleep

import httplib2
from googleapiclient import discovery
from oauth2client.service_account import ServiceAccountCredentials

import xmltodict

import urllib.request

import pandas as pd

import psycopg2
from config import host, port, user, password, db_name
from sqlalchemy import create_engine


CREDENTIALS_FILE = 'creds.json'
spreadsheet_id = '1inELIBAkvAozqu8oSu_6O9vACC9LpcR6k8RT5pzTKYA'

credentials = ServiceAccountCredentials.from_json_keyfile_name(
    CREDENTIALS_FILE,
    ['https://www.googleapis.com/auth/spreadsheets',
     'https://www.googleapis.com/auth/drive'])
httpAuth = credentials.authorize(httplib2.Http())
service = discovery.build('sheets', 'v4', http=httpAuth)

source_spreadsheet_id = '1LTejK-Oo7L1bFreBIIcEZnF1W1RCC1s_jos3EuIP0jI'


def spreadsheet_id_append(source_spreadsheet_id: str):
    values = service.spreadsheets().values().get(
        spreadsheetId=source_spreadsheet_id,
        majorDimension='ROWS',
        range='Лист4'
    ).execute()
    values = values['values']
    df_values = pd.DataFrame(values[1:], columns=values[0])
    df_values["стоимость в руб."] = [float(df_values['стоимость,$'][i]) *
                                     dollar_ruble(list(df_values['срок поставки'][i].split('.'))) for i
                                     in range(len(df_values))]
    return df_values


def spreadsheet_id_update(spreadsheet_id):
    service.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={
            "valueInputOption": "USER_ENTERED",
            "data": [
                {"range": "Лист1",
                 "majorDimension": "ROWS",
                 "values": [item for item in [spreadsheet_id_append(spreadsheet_id).columns.tolist()] + spreadsheet_id_append(spreadsheet_id).values.tolist()]
                 }
            ]
        }
    ).execute()


def dollar_ruble(date: list) -> float:
    url_dollar = "https://www.cbr.ru/scripts/XML_daily.asp?date_req={dd}/{mm}/{gg}"
    file_xml = urllib.request.urlopen(url_dollar.format(dd=date[0], mm=date[1], gg=date[2])).read()
    rubles = xmltodict.parse(file_xml)
    return float(rubles['ValCurs']['Valute'][10]['Value'].replace(',', '.'))


def main():
    while True:
        spreadsheet_id_update(spreadsheet_id)
        DataFrame_to_PostgreSQL(spreadsheet_id_append(spreadsheet_id))
        sleep(1)


def DataFrame_to_PostgreSQL(df_values):
    try:
        connection = psycopg2.connect(
            host=host,
            user=user,
            password=password,
            database=db_name
        )
        connection.autocommit = True

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT version();"
            )

            print(f"Server version: {cursor.fetchone()}")

        engine = create_engine(f'postgresql://{user}:{password}@{host}:{port}/{db_name}')
        df_values.to_sql('numbers_test', con=engine, if_exists='replace', index=False), engine.execute(f"SELECT * FROM numbers_test").fetchall()

    except Exception as _ex:
        print("[INFO] Error while working with PostgreSQL", _ex)
    finally:
        if connection:
            connection.close()

            print("[INFO] PostgreSQL connection closed")


if __name__ == "__main__":
    main()
