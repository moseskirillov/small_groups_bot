import logging
from datetime import datetime

from peewee import fn

from database.db_connection import connect_to_bot
from models.group import Group
from models.group_leader import GroupLeader

HOME_GROUP = 'Метро: <b>{}</b>\nДень: <b>{}</b>\nВремя: <b>{}</b>\nВозраст: <b>{}</b>\nТип: <b>{}</b>\nЛидер: <b>{}</b>\n'


class GroupInfo:
    """
    Обработчик команды старт
    """

    def __init__(self, leader_id, group) -> None:
        self.leader_id = leader_id
        self.group = group


def find_group_by_metro(search_text):
    """
    Ищем и возвращаем ДГ
    """
    try:
        connect_to_bot.connect(reuse_if_open=True)
        logging.info('Выполнено подключение к БД')
        finding_groups = (Group
                          .select()
                          .join(GroupLeader, on=(Group.leader == GroupLeader.id))
                          .where(fn.Lower(Group.metro).contains(search_text))
                          .prefetch(GroupLeader))
        result_groups = []
        for group in finding_groups:
            time_str = datetime.strptime(str(group.time), '%H:%M:%S').strftime('%H:%M')
            home_group = HOME_GROUP.format(group.metro, group.day, time_str, group.age, group.type, group.leader.name)
            result_groups.append(GroupInfo(leader_id=group.leader.id, group=home_group))
        return result_groups
    except Exception as exception:
        logging.error('Ошибка поиска ДГ по запросу %d: %d', search_text, exception)
        return []
    finally:
        connect_to_bot.close()
