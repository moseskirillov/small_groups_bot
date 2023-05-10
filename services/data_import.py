"""
Импорт данных из Хаба и таблицы по домашкам
"""

import logging
import os

import pandas

from database.db_connection import connect_to_bot
from database.db_connection import connect_to_wolrus_hub
from models.group import Group
from models.group_leader import GroupLeader
from models.leader_groups import LeaderGroups
from models.region_leader import RegionLeader
from models.regional_group import RegionalGroupLeaders

TG_DEFAULT = 'Pelna'
URL = 'https://docs.google.com/spreadsheets/d/{}/export?format=csv&gid={}'
SHEET_ID = os.getenv('WOL_HOME_GROUP_SHEET_ID')
GENERAL_TABLE_ID = os.getenv('WOL_HOME_GROUP_GENERAL_ID')

CURSOR = None


def parse_data_from_hub():
    global CURSOR
    try:
        connect_to_bot.connect(reuse_if_open=True)
        CURSOR = connect_to_wolrus_hub.cursor()
        CURSOR.execute('select subway, weekday, time_of_hg, type_age, type_of_hg, name_leader '
                       'from master_data_history_view '
                       'where status_of_hg = \'открыта\'')
        results = CURSOR.fetchall()
        for result in results:
            group_leader = GroupLeader.get_or_none(GroupLeader.name == result[5])
            if group_leader is None:
                group_leader = GroupLeader(name=result[5], telegram=TG_DEFAULT)
                group_leader.save()
            group, _ = Group.get_or_create(
                metro=result[0],
                day=result[1],
                time=result[2],
                leader=group_leader,
                defaults={'age': result[3], 'type': result[4]}
            )
            LeaderGroups.get_or_create(leader=group_leader, group=group)
    except Exception as e:
        logging.error(f"An error occurred while parsing data from hub: {e}")
    finally:
        if CURSOR is not None:
            CURSOR.close()
        connect_to_wolrus_hub.close()
        connect_to_bot.close()


def parse_data_from_tables(table_id):
    try:
        data_from_google = pandas.read_csv(URL.format(SHEET_ID, table_id)).values
        leader_name_cell = 2 if table_id == GENERAL_TABLE_ID else 1
        leader_tg_cell = 4 if table_id == GENERAL_TABLE_ID else 6
        connect_to_bot.connect(reuse_if_open=True)
        for row in data_from_google:
            group_leader = GroupLeader.get_or_none(GroupLeader.name == row[leader_name_cell].strip())
            if group_leader is not None:
                group_leader.telegram = row[leader_tg_cell].replace('@', '')
                group_leader.save()
                regional_leader, created = RegionLeader.get_or_create(name=row[0], defaults={'telegram': ''})
                RegionalGroupLeaders.get_or_create(regional_leader=regional_leader, group_leader=group_leader)
    except Exception as e:
        logging.error(f"An error occurred while parsing data from Google: {e}")
    finally:
        connect_to_bot.close()


def find_leaders_and_save_tg_chat_id(tg_login, chat_id):
    try:
        connect_to_bot.connect(reuse_if_open=True)
        group_leader = GroupLeader.get_or_none(GroupLeader.telegram == tg_login)
        if group_leader is not None:
            group_leader.telegram_id = chat_id
            group_leader.save()
        regional_leader = RegionLeader.get_or_none(RegionLeader.telegram == tg_login)
        if regional_leader is not None:
            regional_leader.telegram_id = chat_id
            regional_leader.save()
    except Exception as e:
        logging.error(f"An error occurred while parsing data from Google: {e}")
    finally:
        connect_to_bot.close()
