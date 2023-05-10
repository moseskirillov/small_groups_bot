"""
Главный модуль
"""
import os

from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler

from bot.handlers import start, data_import, generate_report, search_group, join_to_group
from config import logging_init
from database.db_init import database_init

TOKEN = os.getenv('BOT_TOKEN')


def main() -> None:
    """
    Создаем и запускаем бота
    """
    application = ApplicationBuilder().token(TOKEN).build()

    start_handler = CommandHandler('start', start)
    search_handler = MessageHandler(filters.TEXT & ~filters.Regex(r'Отчет|Импорт'), search_group)
    add_to_group_handler = CallbackQueryHandler(join_to_group, pattern='add_to_group')
    import_handler = MessageHandler(filters.Text(['Импорт']), data_import)
    report_handler = MessageHandler(filters.Text(['Отчет']), generate_report)

    application.add_handler(start_handler)
    application.add_handler(search_handler)
    application.add_handler(add_to_group_handler)
    application.add_handler(import_handler)
    application.add_handler(report_handler)

    application.run_polling()


if __name__ == '__main__':
    logging_init()
    database_init()
    main()
