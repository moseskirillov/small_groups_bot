from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ConversationHandler, ContextTypes, MessageHandler, filters

from database.db_connection import connect_to_bot
from keyboards import search_is_empty_keyboard, PICK_GROUP_TEXT, RETURN_BUTTON_TEXT, join_to_group_keyboard, \
    start_keyboard, conversation_days_keyboard, conversation_age_keyboard, conversation_type_keyboard, \
    conversation_result_keyboard
from models.group_model import Group

DAY, AGE, TYPE, METRO, RESULT = range(5)


def conversation_handler():
    return ConversationHandler(
        entry_points=[MessageHandler(filters.Text([PICK_GROUP_TEXT]), conversation_start)],
        states={
            DAY: [MessageHandler(
                filters.Regex("^(Понедельник|Вторник|Среда|Четверг|Пятница|Суббота|Воскресенье)$"),
                conversation_day
            )],
            AGE: [MessageHandler(
                filters.Regex("^(Взрослые|Молодежные \(до 25\)|Молодежные \(после 25\))$"),
                conversation_age
            )],
            TYPE: [MessageHandler(
                filters.Regex("^(Общая|Мужская|Женская|Семейная|Благовестие)$"),
                conversation_type
            )],
            RESULT: [MessageHandler(filters.Text(['Посмотреть результат']), conversation_result)]
        },
        fallbacks=[MessageHandler(filters.Text([RETURN_BUTTON_TEXT]), conversation_cancel)]
    )


async def conversation_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['in_conversation'] = True
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Выберите день недели, в который вы хотели бы посещать домашнюю группу',
        reply_markup=conversation_days_keyboard,
    )
    return DAY


async def conversation_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    day = update.message.text
    context.user_data['day'] = day
    await update.message.reply_text(
        f'Вы выбрали день недели: {day}\n'
        f'Выберите возраст',
        reply_markup=conversation_age_keyboard
    )
    return AGE


async def conversation_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    day = context.user_data['day']
    age = update.message.text
    context.user_data['age'] = age
    await update.message.reply_text(
        f'Вы выбрали день недели: {day}\n'
        f'Вы выбрали возраст: {age}\n\n'
        f'Выберите тип',
        reply_markup=conversation_type_keyboard
    )
    return TYPE


async def conversation_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    day = context.user_data['day']
    age = context.user_data['age']
    group_type = update.message.text
    context.user_data['type'] = group_type
    await update.message.reply_text(
        f'Вы выбрали день недели: <b>{day}</b>\n'
        f'Вы выбрали возраст: <b>{age}</b>\n'
        f'Вы выбрали тип: <b>{group_type}</b>\n\n'
        f'Нажмите на кнопку внизу, чтобы посмотреть результат',
        reply_markup=conversation_result_keyboard,
        parse_mode=ParseMode.HTML
    )
    return RESULT


async def conversation_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    day = context.user_data['day']
    age = context.user_data['age']
    group_type = context.user_data['type']
    with connect_to_bot.atomic():
        found_groups = Group.select().where((Group.day == day) & (Group.age == age) & (Group.type == group_type))
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
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=home_group,
                    parse_mode=ParseMode.HTML,
                    reply_markup=join_to_group_keyboard
                )
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text='Чтобы искать на другой станции метро, введите ее название или нажмите одну из кнопок',
                reply_markup=start_keyboard
            )
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text='К сожалению, этот поиск не дал результатов.\n'
                     'Можете ввести станцию метро в поиске, '
                     'или посмотреть все домашние группы '
                     '<a href="https://wolrus.org/homegroup">на сайте</a>\n'
                     'Также вы можете связаться с администратором для подбора ближайшей группы',
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
                reply_markup=search_is_empty_keyboard
            )
    context.user_data['in_conversation'] = False
    return ConversationHandler.END


async def conversation_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['in_conversation'] = False
    await update.message.reply_text(
        text='Чтобы найти домашнюю группу, напишите '
             '<b>название станции метро</b>, или нажмите одну из кнопок',
        reply_markup=start_keyboard,
        parse_mode=ParseMode.HTML
    )
    return ConversationHandler.END
