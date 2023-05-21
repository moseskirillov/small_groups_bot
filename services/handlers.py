import html
import json
import logging
import os
import textwrap
import traceback

from peewee import fn
from telegram import Update, ReplyKeyboardRemove
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from data_import import parse_data_from_hub, parse_data_from_google
from database.db_connection import connect_to_bot
from services.keyboards import search_is_empty_keyboard, return_to_start_keyboard, send_contact_keyboard, start_keyboard, \
    join_to_group_keyboard, another_search_keyboard, return_to_start_inline_keyboard
from models.group_leader_model import GroupLeader
from models.group_model import Group
from models.join_request_model import JoinRequest
from models.region_leader_model import RegionLeader
from models.regional_group_model import RegionalGroupLeaders
from models.user_model import User
from services.sheets import add_new_join_request


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['in_conversation'] = False

    with connect_to_bot.atomic():
        User.get_or_create(
            user_id=update.effective_message.from_user.id,
            defaults={
                'first_name': update.effective_chat.first_name,
                'last_name': update.effective_chat.last_name,
                'telegram_login': update.effective_chat.username,
            }
        )

        group_leader = GroupLeader.get_or_none(telegram=update.effective_chat.username)
        if group_leader is not None:
            group_leader.telegram_id = update.effective_message.from_user.id
            group_leader.save()

        regional_leader = RegionLeader.get_or_none(telegram=update.effective_chat.username)
        if regional_leader is not None:
            regional_leader.telegram_id = update.effective_message.from_user.id
            regional_leader.save()

    await update.message.reply_text(
        parse_mode=ParseMode.HTML,
        text=f'Привет, {update.effective_chat.first_name}!\n'
             f'Чтобы найти домашнюю группу, напишите '
             f'<b>название станции метро</b>, или нажмите одну из кнопок',
        reply_markup=start_keyboard
    )


async def search_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('in_conversation'):
        return

    with connect_to_bot.atomic():
        found_groups = (
            Group.select()
            .join(GroupLeader)
            .where(fn.Lower(Group.metro).contains(update.message.text))
            .prefetch(GroupLeader)
        )

    if found_groups:
        for group in found_groups:
            time_str = group.time.strftime('%H:%M')
            home_group = f'Метро: <b>{group.metro}</b>\n' \
                         f'День: <b>{group.day}</b>\nВремя: <b>{time_str}</b>\n' \
                         f'Возраст: <b>{group.age}</b>\n' \
                         f'Тип: <b>{group.type}</b>\n' \
                         f'Лидер: <b>{group.leader.name}</b>'
            context.user_data['home_group_leader_id'] = group.leader
            context.user_data['home_group_info_text'] = home_group
            context.user_data['home_group_is_youth'] = \
                group.age == 'Молодежные (до 25)' or group.age == 'Молодежные (после 25)'
            await update.message.reply_text(
                text=home_group,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
                reply_markup=join_to_group_keyboard
            )

        await update.message.reply_text(
            text='Чтобы искать на другой станции метро, введите ее название или нажмите на одну из кнопок',
            disable_web_page_preview=True,
            reply_markup=another_search_keyboard
        )
    else:
        await update.message.reply_text(
            text='К сожалению, на этой станции пока нет домашних групп.\n'
                 'Можете ввести другую станцию метро, '
                 'или посмотреть все домашние группы '
                 '<a href="https://wolrus.org/homegroup">на сайте</a>\n'
                 'Также вы можете связаться с администратором для подбора ближайшей группы',
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
            reply_markup=search_is_empty_keyboard
        )


async def search_by_button(update: Update, _):
    await update.message.reply_text(
        text='Чтобы найти домашнюю группу, напишите <b>название станции метро</b>',
        parse_mode=ParseMode.HTML,
        reply_markup=return_to_start_inline_keyboard
    )


async def join_to_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Нажмите на кнопку чтобы отправить Ваш контакт и лидер домашней группы свяжется с Вами',
        reply_markup=send_contact_keyboard
    )


async def return_to_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        parse_mode=ParseMode.HTML,
        text='Чтобы найти домашнюю группу, напишите '
             '<b>название станции метро</b>, или нажмите одну из кнопок',
        reply_markup=start_keyboard
    )


async def send_contact_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    is_open_group = context.chat_data.get('open_group')
    ministry_leader_chat_id = os.getenv('MINISTRY_LEADER')

    if is_open_group:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Спасибо! Лидер служения свяжется с Вами',
            disable_web_page_preview=True,
            reply_markup=return_to_start_keyboard
        )
        await context.bot.send_message(
            chat_id=ministry_leader_chat_id,
            text='Новый человек хочет открыть домашнюю группу. Вот его контакт:\n',
        )
        await context.bot.send_contact(
            chat_id=ministry_leader_chat_id,
            contact=update.message.contact
        )
        context.chat_data.clear()
    else:
        group_leader_id = context.user_data['home_group_leader_id']
        group_info_text = context.user_data['home_group_info_text']

        with connect_to_bot.atomic():
            user, _ = User.get_or_create(
                user_id=update.effective_message.from_user.id,
                defaults={
                    'first_name': update.effective_chat.first_name,
                    'last_name': update.effective_chat.last_name,
                    'telegram_login': update.effective_chat.username,
                }
            )
            group_leader = GroupLeader.get(id=group_leader_id)
            regional_leader = (
                RegionLeader
                .select()
                .join(RegionalGroupLeaders)
                .join(GroupLeader)
                .where(GroupLeader.id == group_leader_id)
                .get()
            )
            JoinRequest.create(leader=group_leader, user=user)

        await update.message.reply_text(
            text='Спасибо! Лидер домашней группы свяжется с Вами',
            reply_markup=return_to_start_keyboard
        )

        group_leader_chat_id = group_leader.telegram_id or os.getenv('ADMIN_ID')
        await context.bot.send_message(
            chat_id=group_leader_chat_id,
            text=f'{update.effective_chat.first_name} '
                 f'{update.effective_chat.last_name} '
                 f'хочет присоединиться к Вашей домашней группе. '
                 f'Вот его/ее контакт:',
        )
        await context.bot.send_contact(
            chat_id=group_leader_chat_id,
            contact=update.message.contact
        )

        regional_leader_chat_id = regional_leader.telegram_id or os.getenv('ADMIN_ID')
        await context.bot.send_message(
            chat_id=regional_leader_chat_id,
            text=f'{update.effective_chat.first_name} '
                 f'{update.effective_chat.last_name} '
                 f'хочет присоединиться к домашней группе Вашего региона\n\n'
                 f'Вот информация о группе и контакт человека: \n\n'
                 f'{group_info_text}',
            parse_mode=ParseMode.HTML
        )
        await context.bot.send_contact(
            chat_id=regional_leader_chat_id,
            contact=update.message.contact
        )
        add_new_join_request(
            user.first_name,
            user.last_name,
            user.telegram_login,
            group_leader.name,
            regional_leader.name,
            context.user_data['home_group_is_youth']
        )


async def open_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.chat_data['open_group'] = True
    await update.callback_query.answer()
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Нажмите на кнопку чтобы отправить Ваш контакт и лидер служения домашних групп свяжется с Вами',
        reply_markup=send_contact_keyboard
    )


async def import_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with connect_to_bot:
        user = User.get_or_none(user_id=update.effective_chat.id)
        if user is not None and user.is_admin:
            parse_data_from_hub()
            parse_data_from_google(os.getenv('WOL_HOME_GROUP_GENERAL_ID'))
            parse_data_from_google(os.getenv('WOL_HOME_GROUP_YOUTH_ID'))
            await context.bot.send_message(chat_id=update.effective_chat.id, text='Импорт успешно завершен')
        else:
            await context.bot.send_message(chat_id=update.effective_chat.id, text='У тебя нет прав на эту команду')


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logging.error('Произошла ошибка при работе бота:', exc_info=context.error)
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = ''.join(tb_list)
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    wrapped_traceback = textwrap.wrap(tb_string, width=4096)
    error_message = (
        f'<pre>Произошла ошибка при работе бота\n</pre>'
        f'<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}'
        '</pre>\n\n'
        f'<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n'
        f'<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n'
    )

    with connect_to_bot:
        for i, part in enumerate(wrapped_traceback):
            traceback_message = f'<pre>{html.escape(part)}</pre>'
            message = f'{error_message}\n' \
                      f'<pre>Стек-трейс, часть {i + 1} из ' \
                      f'{len(wrapped_traceback)}</pre>\n\n' \
                      f'{traceback_message}'
            await context.bot.send_message(chat_id=os.getenv('ADMIN_ID'), text=message, parse_mode=ParseMode.HTML)

        await context.bot.send_message(
            chat_id=update.effective_chat.id, text='Произошла ошибка при работе бота. Пожалуйста, попробуйте позже',
            reply_markup=ReplyKeyboardRemove()
        )