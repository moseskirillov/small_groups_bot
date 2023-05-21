from __future__ import print_function

import asyncio
import base64
import logging
import os.path
import re
from datetime import datetime
from html.parser import HTMLParser

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from telegram import Bot
from telegram.error import NetworkError

from database.db_connection import connect_to_bot
from models.group_leader_model import GroupLeader
from models.region_leader_model import RegionLeader
from models.regional_group_model import RegionalGroupLeaders
from models.site_request_model import SiteRequest
from sheets import add_new_site_request

TOKEN = 'token.json'
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


def google_creds_check():
    creds = None
    if os.path.exists(TOKEN):
        creds = Credentials.from_authorized_user_file(TOKEN, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                '../gmail_creds.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN, 'w') as token:
            token.write(creds.to_json())
    return creds


def get_and_parse_mails():
    creds = google_creds_check()
    try:
        service = build('gmail', 'v1', credentials=creds)
        results = service.users().messages().list(userId='me', maxResults=30).execute()
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

            if 'body' in payload and subject == 'Домашняя группа':
                site_request = create_to_table_request(payload, date)
                add_new_site_request(site_request)
                asyncio.run(send_site_request_to_leader(site_request))

    except HttpError as error:
        logging.error(f'Произошла ошибка парсинга писем по заявкам ДГ с почты: {error}')


class HTMLTagStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stripped_text = []

    def handle_data(self, data):
        self.stripped_text.append(data)


def create_to_table_request(payload, date):
    date_format = "%a, %d %b %Y %H:%M:%S %z (%Z)"
    date_obj = datetime.strptime(date, date_format)
    formatted_date = date_obj.strftime("%d.%m.%Y")

    tag_stripper = HTMLTagStripper()
    body = base64.urlsafe_b64decode(payload['body']['data']).decode()
    tag_stripper.feed(body)
    stripped_text = ' '.join(tag_stripper.stripped_text)
    name = re.search(r'Имя\s+(\S+)', stripped_text, re.IGNORECASE).group(1)
    surname = re.search(r'Фамилия\s+(\S+)', stripped_text, re.IGNORECASE).group(1)
    age = re.search(r'Полных\s+лет\s+\(Возраст\)\s+(\S+)', stripped_text, re.IGNORECASE).group(1)
    city = re.search(r'Город\s+(\S+)', stripped_text, re.IGNORECASE).group(1)
    email = re.search(r'E-mail\s+(\S+)', stripped_text, re.IGNORECASE).group(1)
    phone = re.search(r'Телефон\s+(\S+)', stripped_text, re.IGNORECASE).group(1)
    group = re.search(r'ВЫБРАННАЯ\s+ДОМАШНЯЯ\s+ГРУППА\s+(\S+\s+\S+)', stripped_text, re.IGNORECASE).group(1)

    return SiteRequest(formatted_date, name, surname, age, city, email, phone, group)


async def send_site_request_to_leader(request: SiteRequest):
    with connect_to_bot.atomic():
        group_leader = GroupLeader.get(name=request.group)
        regional_leader = (
            RegionLeader
            .select()
            .join(RegionalGroupLeaders)
            .join(GroupLeader)
            .where(GroupLeader.id == group_leader)
            .get()
        )
    async with Bot(os.getenv('BOT_TOKEN')) as bot:
        try:
            await bot.send_message(
                chat_id=os.getenv('ADMIN_ID'),
                text=f'{request.name} '
                     f'{request.surname}'
                     f'хочет присоединиться к Вашей домашней группе. '
                     f'Вот его/ее контакт:',
            )
            await bot.send_contact(
                chat_id=os.getenv('ADMIN_ID'),
                phone_number=request.phone
            )
        except NetworkError:
            await asyncio.sleep(1)


if __name__ == '__main__':
    get_and_parse_mails()
