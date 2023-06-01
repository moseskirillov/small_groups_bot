import os

import pandas

from database.db_connection import connect_to_wolrus_hub, connect_to_bot
from models.group_leader_model import GroupLeader
from models.group_model import Group
from models.leader_groups_model import LeaderGroups
from models.region_leader_model import RegionLeader
from models.regional_group_model import RegionalGroupLeaders

TG_DEFAULT = 'Pelna'
SHEET_ID = os.getenv('WOL_HOME_GROUP_SHEET_ID')
GENERAL_TABLE_ID = os.getenv('WOL_HOME_GROUP_GENERAL_ID')
URL = 'https://docs.google.com/spreadsheets/d/{}/export?format=csv&gid={}'


def parse_data_from_hub():
    with connect_to_wolrus_hub:
        with connect_to_wolrus_hub.cursor() as cursor:
            cursor.execute('SELECT subway, weekday, time_of_hg, type_age, type_of_hg, name_leader '
                           'FROM master_data_history_view '
                           'WHERE status_of_hg = \'открыта\'')
            results = cursor.fetchall()
            for result in results:
                group_leader = GroupLeader.get_or_none(GroupLeader.name == result[5])
                if group_leader is None:
                    group_leader = GroupLeader(name=result[5], telegram=TG_DEFAULT)
                    group_leader.save()
                group, _ = Group.get_or_create(
                    metro=result[0],
                    day=result[1],
                    time=result[2],
                    age=result[3],
                    type=result[4],
                    is_open=True,
                    leader=group_leader
                )
                LeaderGroups.get_or_create(leader=group_leader, group=group)


def check_open_groups():
    with connect_to_wolrus_hub:
        with connect_to_wolrus_hub.cursor() as cursor:
            groups = Group.select().join(LeaderGroups).join(GroupLeader)
            for group in groups:
                cursor.execute(f'SELECT status_of_hg '
                               f'FROM master_data_history_view '
                               f'WHERE name_leader = \'{group.leader.name}\' '
                               f'AND weekday = \'{group.day}\' '
                               f'AND time_of_hg = \'{group.time}\' '
                               f'AND subway = \'{group.metro}\' '
                               f'AND type_age = \'{group.age}\' '
                               f'AND type_of_hg = \'{group.type}\'')
                result = cursor.fetchone()
                if result:
                    group_status = result[0]
                    if group_status is None or group_status != 'открыта':
                        group.is_open = False
                        group.save()


def parse_data_from_google(table_id):
    data_from_google = pandas.read_csv(URL.format(SHEET_ID, table_id)).values
    leader_name_cell = 2 if table_id == GENERAL_TABLE_ID else 1
    leader_tg_cell = 4 if table_id == GENERAL_TABLE_ID else 6
    with connect_to_bot.atomic():
        for row in data_from_google:
            group_leader = GroupLeader.get_or_none(GroupLeader.name == row[leader_name_cell].strip())
            if group_leader is not None:
                group_leader.telegram = row[leader_tg_cell].replace('@', '')
                group_leader.save()
                regional_leader, _ = RegionLeader.get_or_create(name=row[0], defaults={'telegram': ''})
                RegionalGroupLeaders.get_or_create(regional_leader=regional_leader, group_leader=group_leader)
