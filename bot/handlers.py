"""
Все обработчики бота
"""
import os

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from services.data_import import find_leaders_and_save_tg_chat_id
from services.data_import import parse_data_from_hub, parse_data_from_tables
from services.groups_service import find_group_by_metro
from services.join_service import join_to_group_process
from services.reports_service import get_report
from services.user_service import save_or_check_user

GENERAL_TABLE_ID = os.getenv('WOL_HOME_GROUP_GENERAL_ID')
YOUTH_TABLE_ID = os.getenv('WOL_HOME_GROUP_YOUTH_ID')

HELLO_MESSAGE = 'Привет, {}! \nЧтобы найти домашнюю группу, напишите ближайшую станцию метро'
IMPORT_SUCCESS = 'Команда импорта выполнена'
SEARCH_ANOTHER_GROUP = 'Для нового поиска, напишите другую станцию метро'
GROUP_NOT_FOUND = 'К сожалению, на этой станции пока нет домашних групп.\nМожете ввести другую станцию метро,\n' \
                  'Также все домашние группы можно посмотреть\n<a href="https://wolrus.org/homegroup">на сайте</a>\n' \
                  'Также вы можете связаться с администратором для подбора ближайшей группы'
BOT_ERROR_TEXT = 'Произошла ошибка. Пожалуйста, попробуйте позже или напишите администратору'

REPORT_ERROR_TEXT = 'Отчет пустой или произошла ошибка при генерации'


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды старт
    """
    admin_buttons = []
    first_name = update.effective_chat.first_name
    last_name = update.effective_chat.last_name
    user_name = f'{"" if first_name is None else first_name} {"" if last_name is None else last_name}'
    user = save_or_check_user(user_name, update.effective_message.from_user.id, update.effective_chat.username)
    if user and user.is_admin:
        admin_buttons.append([KeyboardButton('Отчет'), KeyboardButton('Импорт')])
    find_leaders_and_save_tg_chat_id(update.effective_chat.username, update.effective_message.from_user.id)
    await context.bot.send_message(
        text=HELLO_MESSAGE.format(f'{user_name}'),
        chat_id=update.effective_chat.id,
        reply_markup=ReplyKeyboardMarkup(admin_buttons, resize_keyboard=True)
    )


async def search_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды поиска ДГ
    """
    groups = find_group_by_metro(update.message.text)
    if len(groups) > 0:
        for group_info in groups:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=group_info.group,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(
                        'Присоединиться',
                        callback_data=f'add_to_group_{group_info.leader_id}'
                    )
                ]])
            )
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            disable_web_page_preview=True,
            text=SEARCH_ANOTHER_GROUP,
            parse_mode=ParseMode.HTML
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=GROUP_NOT_FOUND,
            disable_web_page_preview=True,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    'Написать администратору',
                    url='https://t.me/Pelna'
                )
            ]])
        )


async def join_to_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды присединения к ДГ
    """
    group_info_text, group_leader = join_to_group_process(update)
    if group_info_text is not None and group_leader is not None:
        first_name = update.effective_chat.first_name
        last_name = update.effective_chat.last_name
        user_name = f'{"" if first_name is None else first_name} {"" if last_name is None else last_name}'
        await update.callback_query.answer()
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=group_info_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton('Написать', url=f'https://t.me/{group_leader.telegram}')]
            ]), parse_mode=ParseMode.HTML
        )
        await context.bot.send_message(
            chat_id=group_leader.telegram_id,
            text=f'Пользователь {user_name} нажал(а) на кнопку Присоединиться к Вашей домашней группе. Он(а) может '
                 f'написать Вам.',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton('Написать ему', url=f'https://t.me/{update.effective_chat.username}')]
            ])
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=BOT_ERROR_TEXT,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton('Написать администратору', url='https://t.me/moses_kirillov')]
            ])
        )


async def data_import(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды импорта данных с базы Хаба и Google Sheet
    """
    parse_data_from_hub()
    parse_data_from_tables(GENERAL_TABLE_ID)
    parse_data_from_tables(YOUTH_TABLE_ID)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=IMPORT_SUCCESS)


async def generate_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды получения отчетов
    """
    report_text = get_report()
    if report_text is not None and len(report_text) > 0:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=''.join(report_text),
            parse_mode=ParseMode.HTML
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=REPORT_ERROR_TEXT,
            parse_mode=ParseMode.HTML
        )
