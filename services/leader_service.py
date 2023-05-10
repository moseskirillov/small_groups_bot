import logging

from database.db_connection import connect_to_bot
from models.group_leader import GroupLeader


def find_leader_by_id(leader_id):
    try:
        connect_to_bot.connect(reuse_if_open=True)
        logging.info('Выполнено подключение к БД')
        leader = GroupLeader.get_by_id(leader_id)
        logging.info(f'Поиск завершен. Найден лидер {leader.name}')
        return leader
    except Exception as e:
        logging.error(f"Ошибка поиска лидера с id {leader_id}: {e}")
        return None
    finally:
        connect_to_bot.close()
