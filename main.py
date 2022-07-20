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

# Подключаемся к моей гугл таблице
CREDENTIALS_FILE = 'creds.json'
spreadsheet_id = '1inELIBAkvAozqu8oSu_6O9vACC9LpcR6k8RT5pzTKYA'

credentials = ServiceAccountCredentials.from_json_keyfile_name(
    CREDENTIALS_FILE,
    ['https://www.googleapis.com/auth/spreadsheets',
     'https://www.googleapis.com/auth/drive'])
httpAuth = credentials.authorize(httplib2.Http())
service = discovery.build('sheets', 'v4', http=httpAuth)

source_spreadsheet_id = '1f-qZEX1k_3nj5cahOzntYAnvO4ignbyesVO7yuBdv_g'


def spreadsheet_id_append(source_spreadsheet_id: str):  # Читаем таблицу из тестового задания, добавляем в неё нужную колонку и возвращаем DataFrame для дальнейшей работы
    values = service.spreadsheets().values().get(
        spreadsheetId=source_spreadsheet_id,
        majorDimension='ROWS',
        range='Лист1'
    ).execute()
    values = values['values']
    df_values = pd.DataFrame(values[1:], columns=values[0])
    df_values["стоимость в руб."] = [float(df_values['стоимость,$'][i]) *
                                     dollar_ruble(list(df_values['срок поставки'][i].split('.'))) for i
                                     in range(len(df_values))]
    return df_values


def spreadsheet_id_update(source_spreadsheet_id, spreadsheet_id):  # Перезаписываем мою таблицу, использую DataFrame
    service.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={
            "valueInputOption": "USER_ENTERED",
            "data": [
                {"range": "Лист1",
                 "majorDimension": "ROWS",
                 "values": [item for item in [spreadsheet_id_append(source_spreadsheet_id).columns.tolist()] + spreadsheet_id_append(source_spreadsheet_id).values.tolist()]
                 }
            ]
        }
    ).execute()


def dollar_ruble(date: list) -> float:  # Возвращаем курс доллара в определенную дату
    url_dollar = "https://www.cbr.ru/scripts/XML_daily.asp?date_req={dd}/{mm}/{gg}"
    file_xml = urllib.request.urlopen(url_dollar.format(dd=date[0], mm=date[1], gg=date[2])).read()
    rubles = xmltodict.parse(file_xml)
    return float(rubles['ValCurs']['Valute'][10]['Value'].replace(',', '.'))


def dataframe_to_postgresql(df_values):  # Записываем DataFrame в таблицу postgresql
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


def main():  # Моя основная логика программы
    while True:
        spreadsheet_id_update(source_spreadsheet_id, spreadsheet_id)
        dataframe_to_postgresql(spreadsheet_id_append(spreadsheet_id))
        sleep(1)


if __name__ == "__main__":
    main()
