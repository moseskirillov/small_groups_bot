import logging
import os
from datetime import datetime

import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ['https://www.googleapis.com/auth/spreadsheets', "https://www.googleapis.com/auth/drive"]
credentials_path = os.path.join("..", "google_creeds.json")
credentials = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scope)


def add_new_join_request(name, lastname, telegram, leader, district_leader, is_youth):
    client = gspread.authorize(credentials)
    spreadsheet = client.open("Заявки на домашние группы")
    worksheet = spreadsheet.worksheet('Молодежные заявки' if is_youth else 'Общие заявки')
    values = worksheet.get_all_values()
    first_empty_row = len(values) + 1
    worksheet.update_cell(first_empty_row, 1, datetime.now().strftime("%d.%m.%Y"))
    worksheet.update_cell(first_empty_row, 2, name)
    worksheet.update_cell(first_empty_row, 3, lastname)
    worksheet.update_cell(first_empty_row, 4, telegram)
    worksheet.update_cell(first_empty_row, 5, leader)
    worksheet.update_cell(first_empty_row, 6, district_leader)
    logging.info('Добавлено новое значение в таблицу заявок в ДГ')

# sheet.share('moisey.kirillov@gmail.com', perm_type='user', role='writer')
