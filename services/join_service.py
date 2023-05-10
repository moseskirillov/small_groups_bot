import logging

from database.db_connection import connect_to_bot
from models.join_request import JoinRequest
from services.leader_service import find_leader_by_id
from services.user_service import get_user_by_login


def join_to_group_process(update):
    """
    Поиск лидера и генерация ответа для пользователя
    """
    group_leader = find_leader_by_id(update.callback_query.data[13:])
    if group_leader is not None:
        try:
            user = get_user_by_login(update.effective_chat.username)
            if user is not None:
                connect_to_bot.connect(reuse_if_open=True)
                logging.info('Выполнено подключение к БД')
                response = f'Лидер данной домашней группы <b>{group_leader.name}</b>. Чтобы написать лидеру, нажмите ' \
                           f'на кнопку ниже'
                JoinRequest.create(leader=group_leader, user=user)
                return response, group_leader
        except Exception as exception:
            logging.error(f'Ошибка сохранения запроса на присоединение к ДГ: {exception}')
            return None
        finally:
            connect_to_bot.close()
    else:
        return None
