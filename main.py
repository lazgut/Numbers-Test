from time import sleep

from pprint import pprint

import httplib2
from googleapiclient import discovery
from oauth2client.service_account import ServiceAccountCredentials

CREDENTIALS_FILE = 'creds.json'
spreadsheet_id = '1inELIBAkvAozqu8oSu_6O9vACC9LpcR6k8RT5pzTKYA'

credentials = ServiceAccountCredentials.from_json_keyfile_name(
    CREDENTIALS_FILE,
    ['https://www.googleapis.com/auth/spreadsheets',
     'https://www.googleapis.com/auth/drive'])
httpAuth = credentials.authorize(httplib2.Http())
service = discovery.build('sheets', 'v4', http=httpAuth)

source_spreadsheet_id = '1LTejK-Oo7L1bFreBIIcEZnF1W1RCC1s_jos3EuIP0jI'

"""  copyTO()
target_spreadsheet_id = spreadsheet_id
sheet_id = 0
request = service.spreadsheets().sheets().copyTo(
    spreadsheetId=source_spreadsheet_id,
    sheetId=sheet_id,
    body={'destinationSpreadsheetId': target_spreadsheet_id}
)"""


def spreadsheet_id_update(source_spreadsheet_id, spreadsheet_id):
    values = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        majorDimension='ROWS',
        range='Лист4'
    ).execute()
    pprint(values)
    values_tmp = service.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={
            "valueInputOption": "USER_ENTERED",
            "data": [
                {"range": "Лист1!A1:D51",
                 "majorDimension": "ROWS",
                 "values": [item for item in values['values']]
                 }
            ]
        }
    ).execute()
    pprint(values_tmp)


if __name__ == "__main__":
    while True:
        spreadsheet_id_update(source_spreadsheet_id, spreadsheet_id)
        sleep(1)
