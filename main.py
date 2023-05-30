import os

from telegram.ext import ApplicationBuilder, CommandHandler, filters, MessageHandler, CallbackQueryHandler

from config import logging_init
from database.db_init import database_init
from services.conversation import conversation_handler
from services.handlers import start, search_group, return_to_start, search_by_button, join_to_group, \
    send_contact_response, open_group, error_handler, import_data, check_groups
from services.keyboards import WRITE_METRO_TEXT

TOKEN = os.getenv('BOT_TOKEN')


def handlers_register(bot):
    bot.add_handler(conversation_handler())
    bot.add_handler(CommandHandler('start', start))
    bot.add_handler(CallbackQueryHandler(return_to_start, pattern='return_to_start'))
    bot.add_handler(CallbackQueryHandler(open_group, pattern='open_group'))
    bot.add_handler(MessageHandler(filters.Text([WRITE_METRO_TEXT]), search_by_button))
    bot.add_handler(CallbackQueryHandler(join_to_group, pattern='join_to_group'))
    bot.add_handler(MessageHandler(filters.Text(['Вернуться']), return_to_start))
    bot.add_handler(MessageHandler(filters.CONTACT, send_contact_response))
    bot.add_handler(CallbackQueryHandler(open_group, pattern='open_group'))
    bot.add_handler(CommandHandler('import', import_data))
    bot.add_handler(CommandHandler('check', check_groups))
    bot.add_handler(MessageHandler(filters.TEXT, search_group))
    bot.add_error_handler(error_handler)


def main():
    bot = ApplicationBuilder().token(TOKEN).build()
    handlers_register(bot)
    bot.run_webhook(
        listen='0.0.0.0',
        port=5000,
        url_path='smallgroups',
        webhook_url='https://1493881-cr74590.tw1.ru/smallgroups',
    )


if __name__ == '__main__':
    logging_init()
    database_init()
    main()
