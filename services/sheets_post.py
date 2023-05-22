import logging
import os
from datetime import datetime

import gspread
from oauth2client.service_account import ServiceAccountCredentials

current_dir = os.getcwd()
creds_file_path = os.path.join(current_dir, 'google_creds.json')

scope = ['https://www.googleapis.com/auth/spreadsheets', "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name(creds_file_path, scope)


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


def add_new_site_request(request):
    client = gspread.authorize(credentials)
    spreadsheet = client.open("Заявки на домашние группы")
    worksheet = spreadsheet.worksheet('Заявки с сайта')
    values = worksheet.get_all_values()
    cell_values = request.to_list()
    first_empty_row = len(values) + 1
    for index, value in enumerate(cell_values):
        worksheet.update_cell(first_empty_row, index + 1, value)
    logging.info('Добавлено новое значение в таблицу заявок в ДГ')

# sheet.share('moisey.kirillov@gmail.com', perm_type='user', role='writer')
