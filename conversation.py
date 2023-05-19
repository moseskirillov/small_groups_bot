from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters

from database.db_connection import connect_to_bot
from models.group_model import Group

DAY, AGE, TYPE, METRO, RESULT = range(5)
PICK_GROUP_TEXT = 'Подобрать группу'
CANCEL_TEXT = 'Отменить'


def conv_handler():
    handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Text([PICK_GROUP_TEXT]), pick_up_start)],
        states={
            DAY: [MessageHandler(filters.Regex("^(Понедельник|Вторник|Среда|Четверг|Пятница|Суббота|Воскресенье)$"),
                                 pick_up_day)],
            AGE: [MessageHandler(filters.Regex("^(Взрослые|Молодежные \(до 25\)|Молодежные \(после 25\))$"),
                                 pick_up_age)],
            TYPE: [MessageHandler(filters.Regex("^(Общая|Мужская|Женская|Семейная|Благовестие)$"),
                                  pick_up_type)],
            RESULT: [MessageHandler(filters.Text(['Посмотреть результат']), pick_up_result)]
        },
        fallbacks=[MessageHandler(filters.Text([CANCEL_TEXT]), pick_up_cancel)]
    )
    return handler


async def pick_up_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['in_conversation'] = True
    reply_keyboard = [
        ['Понедельник', 'Вторник'],
        ['Среда', 'Четверг', 'Пятница'],
        ['Суббота', 'Воскресенье'],
        [CANCEL_TEXT]
    ]
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Выберите день недели, в который вы хотели бы посещать домашнюю группу',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            one_time_keyboard=True,
            input_field_placeholder='Выберите день недели',
            resize_keyboard=True
        ),
    )
    return DAY


async def pick_up_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    day = update.message.text
    context.user_data['day'] = day
    await update.message.reply_text(
        f'Вы выбрали день недели: {day}\n'
        f'Выберите возраст',
        reply_markup=ReplyKeyboardMarkup([
            ['Взрослые'], ['Молодежные (до 25)'], ['Молодежные (после 25)'], [CANCEL_TEXT]
        ], resize_keyboard=True)
    )
    return AGE


async def pick_up_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    day = context.user_data['day']
    age = update.message.text
    context.user_data['age'] = age
    keyword = [
        ['Общая', 'Мужская', 'Женская'], ['Семейная', 'Благовестие'], [CANCEL_TEXT]
    ]
    await update.message.reply_text(
        f'Вы выбрали день недели: {day}\n'
        f'Вы выбрали возраст: {age}\n\n'
        f'Выберите тип',
        reply_markup=ReplyKeyboardMarkup(keyword, resize_keyboard=True)
    )
    return TYPE


async def pick_up_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    day = context.user_data['day']
    age = context.user_data['age']
    group_type = update.message.text
    context.user_data['type'] = group_type
    await update.message.reply_text(
        f'Вы выбрали день недели: <b>{day}</b>\n'
        f'Вы выбрали возраст: <b>{age}</b>\n'
        f'Вы выбрали тип: <b>{group_type}</b>\n\n'
        f'Нажмите на кнопку внизу, чтобы посмотреть результат',
        reply_markup=ReplyKeyboardMarkup([['Посмотреть результат']], one_time_keyboard=True, resize_keyboard=True),
        parse_mode=ParseMode.HTML
    )
    return RESULT


async def pick_up_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=home_group,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton('Присоединиться', callback_data='join_to_group')]
                    ])
                )
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text='Чтобы искать на другой станции метро, введите ее название или нажмите на кнопку подбора',
                disable_web_page_preview=True,
                reply_markup=ReplyKeyboardMarkup([[KeyboardButton(text=PICK_GROUP_TEXT)]], resize_keyboard=True)
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
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton('Написать администратору', url='https://t.me/kirillsemiletov')],
                    [InlineKeyboardButton('Открыть свою группу', callback_data='open_group')]
                ])
            )
    context.user_data['in_conversation'] = False
    return ConversationHandler.END


async def pick_up_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['in_conversation'] = False
    await update.message.reply_text(
        'Чтобы найти домашнюю группу, напишите название станции метро, или нажмите кнопку внизу для подбора',
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton(text=PICK_GROUP_TEXT)]], resize_keyboard=True)
    )
    return ConversationHandler.END
