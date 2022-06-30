from time import sleep

import httplib2
from googleapiclient import discovery
from oauth2client.service_account import ServiceAccountCredentials

import xmltodict

import urllib.request

import pandas as pd

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
    return [df_values.columns.tolist()] + df_values.values.tolist()


def spreadsheet_id_update(spreadsheet_id):
    service.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={
            "valueInputOption": "USER_ENTERED",
            "data": [
                {"range": "Лист1",
                 "majorDimension": "ROWS",
                 "values": [item for item in spreadsheet_id_append(spreadsheet_id)]
                 }
            ]
        }
    ).execute()


def dollar_ruble(date: list) -> float:
    url_dollar = "https://www.cbr.ru/scripts/XML_daily.asp?date_req={dd}/{mm}/{gg}"
    file_xml = urllib.request.urlopen(url_dollar.format(dd=date[0], mm=date[1], gg=date[2])).read()
    rubles = xmltodict.parse(file_xml)
    return float(rubles['ValCurs']['Valute'][10]['Value'].replace(',', '.'))


if __name__ == "__main__":
    while True:
        spreadsheet_id_update(spreadsheet_id)
        sleep(1)

