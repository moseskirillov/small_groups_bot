from __future__ import print_function

import base64
import logging
import os.path
import re
from datetime import datetime, timedelta

import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from database.db_connection import connect_to_bot
from models.group_leader_model import GroupLeader
from models.html_tag_stripper_model import HTMLTagStripper
from models.regional_group_model import RegionalGroupLeaders
from models.site_request_model import SiteRequest
from services.sheets_post import add_new_site_request

current_dir = os.getcwd()
creds_file_path = os.path.join(current_dir, 'google_creds.json')
token_file_path = os.path.join(current_dir, 'token.json')
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


def google_creds_check():
    creds = None
    if os.path.exists(token_file_path):
        creds = Credentials.from_authorized_user_file(token_file_path, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(creds_file_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_file_path, 'w') as token:
            token.write(creds.to_json())
    return creds


def get_and_parse_mails():
    creds = google_creds_check()
    try:
        service = build('gmail', 'v1', credentials=creds)

        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)
        formatted_date_yesterday = yesterday.strftime("%Y/%m/%d").replace('/', '/')
        formatted_date_today = today.strftime("%Y/%m/%d").replace('/', '/')
        tomorrow_date_today = tomorrow.strftime("%Y/%m/%d").replace('/', '/')

        results = service \
            .users() \
            .messages() \
            .list(userId='me', q=f'after:{formatted_date_yesterday} before:{tomorrow_date_today}') \
            .execute()
        messages = results.get('messages')

        if not messages:
            return

        for message in messages:
            payload = service.users().messages().get(userId='me', id=message['id']).execute()['payload']
            headers = payload['headers']

            date = ''
            subject = ''

            for header in headers:
                name = header['name']
                value = header['value']
                if name.lower() == 'subject':
                    subject = value
                elif name.lower() == 'date':
                    date = value

            if 'body' in payload and (subject == 'Домашняя группа' or subject == 'Регистрация на Домашнюю группу'):
                site_request = create_to_table_request(payload, date)
                add_new_site_request(site_request)
                send_site_request_to_leader(site_request)

    except HttpError as error:
        logging.error(f'Произошла ошибка парсинга писем по заявкам ДГ с почты: {error}')


def extract_field_from_text(pattern, text):
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return match.group(1)
    return None


def create_to_table_request(payload, date):
    date_obj = datetime.strptime(date, "%a, %d %b %Y %H:%M:%S %z (%Z)")
    formatted_date = date_obj.strftime("%d.%m.%Y")
    tag_stripper = HTMLTagStripper()
    body = base64.urlsafe_b64decode(payload['body']['data']).decode()
    tag_stripper.feed(body)
    stripped_text = ' '.join(tag_stripper.stripped_text)

    name = extract_field_from_text(r'Имя\s+(\S+)', stripped_text)
    surname = extract_field_from_text(r'Фамилия\s+(\S+)', stripped_text)
    age = extract_field_from_text(r'Полных\s+лет\s+\(Возраст\)\s+(\S+)', stripped_text)
    city = extract_field_from_text(r'Город\s+(\S+)', stripped_text)
    email = extract_field_from_text(r'E-mail\s+(\S+)', stripped_text)
    phone = extract_field_from_text(r'Телефон\s+(\S+)', stripped_text)
    group_parts = extract_field_from_text(r'ВЫБРАННАЯ\s+ДОМАШНЯЯ\s+ГРУППА\s+(\S+\s+\S+)', stripped_text)

    if group_parts:
        first_name, last_name = group_parts.split()
        group = f'{last_name} {first_name}'
    else:
        group = None

    return SiteRequest(formatted_date, name, surname, age, city, email, phone, group)


def send_site_request_to_leader(request: SiteRequest):
    with connect_to_bot.atomic():
        group_leader = GroupLeader.get(name=request.group)

        regional_group_leader = (RegionalGroupLeaders
                                 .select()
                                 .join(GroupLeader)
                                 .where(GroupLeader.id == group_leader)
                                 .get())

        message_to_group_leader = 'С сайта пришла заявка на присоединение ' \
                                  'к домашней группе. Контакт человека:'
        message_to_regional_leader = f'С сайта пришла заявка на присоединение ' \
                                     f'к домашней группе лидера по имени {group_leader.name}. Контакт человека:'

        response_text_to_group_leader = send_message(group_leader.telegram_id, message_to_group_leader)
        response_contact_to_group_leader = send_contact(group_leader.telegram_id, request.phone, request.name,
                                                        request.surname)

        check_response(response_text_to_group_leader)
        check_response(response_contact_to_group_leader)

        regional_leader = regional_group_leader.regional_leader

        response_text_to_regional_leader = send_message(regional_leader.telegram_id, message_to_regional_leader)
        response_contact_to_regional_leader = send_contact(regional_leader.telegram_id, request.phone, request.name,
                                                           request.surname)

        check_response(response_text_to_regional_leader)
        check_response(response_contact_to_regional_leader)


def send_message(chat_id, text):
    bot_token = os.getenv("BOT_TOKEN")
    response = requests.get(
        f'https://api.telegram.org/bot{bot_token}/sendMessage',
        params={
            'chat_id': chat_id,
            'text': text
        }
    )
    return response


def send_contact(chat_id, phone_number, first_name, last_name):
    bot_token = os.getenv("BOT_TOKEN")
    response = requests.post(
        f'https://api.telegram.org/bot{bot_token}/sendContact',
        json={
            'chat_id': chat_id,
            'phone_number': phone_number,
            'first_name': first_name,
            'last_name': last_name
        }
    )
    return response


def check_response(response):
    if response.status_code == 200:
        logging.info('Сообщение успешно отправлено.')
    else:
        logging.error('Произошла ошибка при отправке сообщения.')
        logging.error(response.json())
