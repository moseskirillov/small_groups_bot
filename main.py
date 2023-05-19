"""
Модуль запуска
"""
import os

from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler

from config import logging_init
from conversation import conv_handler
from database.db_init import database_init
from handlers import start, search_group, join_to_group, send_contact_response, error_handler, import_data, open_group

SHEET_ID = os.getenv('WOL_HOME_GROUP_SHEET_ID')
YOUTH_TABLE_ID = os.getenv('WOL_HOME_GROUP_YOUTH_ID')
GENERAL_TABLE_ID = os.getenv('WOL_HOME_GROUP_GENERAL_ID')

TOKEN = os.getenv('BOT_TOKEN')


def handlers_register(bot):
    """
    Добавление всех хендлеров
    """
    bot.add_handler(conv_handler())
    bot.add_handler(CommandHandler('start', start))
    bot.add_handler(CommandHandler('import', import_data))
    bot.add_handler(MessageHandler(filters.Text(['Искать домашнюю группу']), start))
    bot.add_handler(CallbackQueryHandler(join_to_group, pattern='join_to_group'))
    bot.add_handler(CallbackQueryHandler(open_group, pattern='open_group'))
    bot.add_handler(MessageHandler(filters.TEXT, search_group))
    bot.add_handler(MessageHandler(filters.CONTACT, send_contact_response))
    bot.add_error_handler(error_handler)


def main():
    """
    Старт бота
    """
    bot = ApplicationBuilder().token(TOKEN).build()
    handlers_register(bot)
    bot.run_polling()


if __name__ == '__main__':
    logging_init()
    database_init()
    main()
