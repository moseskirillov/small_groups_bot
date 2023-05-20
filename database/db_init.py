from database.db_connection import connect_to_bot
from models.group_leader_model import GroupLeader
from models.group_model import Group
from models.join_request_model import JoinRequest
from models.leader_groups_model import LeaderGroups
from models.region_leader_model import RegionLeader
from models.regional_group_model import RegionalGroupLeaders
from models.user_model import User


def database_init():
    tables = [User, RegionLeader, GroupLeader, RegionalGroupLeaders, Group, LeaderGroups, JoinRequest]
    with connect_to_bot:
        for table in tables:
            table.create_table(safe=True)
