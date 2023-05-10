import logging

from database.db_connection import connect_to_bot
from models.user import User


def save_or_check_user(username, telegram_id, telegram_login):
    """
    Если пользователь новый, сохраняем его данные в БД
    """
    try:
        connect_to_bot.connect(reuse_if_open=True)
        user, created = User.get_or_create(username=username, telegram_id=telegram_id, telegram_login=telegram_login)
        if created:
            logging.info(f'Сохранен новый пользователь {username}')
        else:
            logging.info(f'Вошел существующий пользователь {username}')
        return user
    except Exception as exception:
        logging.error(f'Ошибка сохранения пользователя {username}: {exception}')
        return None
    finally:
        connect_to_bot.close()


def get_user_by_login(username):
    """
    Ищем и возвращаем пользователя по логину
    """
    try:
        connect_to_bot.connect(reuse_if_open=True)
        return User.get_or_none(telegram_login=username)
    except Exception as exception:
        logging.error(f'Ошибка поиска пользователя по логину: {username}', exception)
        return None
    finally:
        connect_to_bot.close()
