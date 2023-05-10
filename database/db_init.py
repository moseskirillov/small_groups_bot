import logging

from database.db_connection import connect_to_bot
from models.group import Group
from models.group_leader import GroupLeader
from models.join_request import JoinRequest
from models.leader_groups import LeaderGroups
from models.region_leader import RegionLeader
from models.regional_group import RegionalGroupLeaders
from models.user import User


def database_init():
    """
    Проверяет и создает таблицы
    """
    tables = [User, RegionLeader, GroupLeader, RegionalGroupLeaders, Group, LeaderGroups, JoinRequest]
    try:
        connect_to_bot.connect(reuse_if_open=True)
        logging.info('Выполнено подключение к БД')
        for table in tables:
            table.create_table(safe=True)
        logging.info('Проверка и создание таблиц завершены')
    except Exception as exception:
        logging.error('An error occurred while parsing data from hub: %d', exception)
    finally:
        connect_to_bot.close()
