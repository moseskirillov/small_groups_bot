from peewee import Model, PrimaryKeyField, ForeignKeyField

from database.db_connection import connect_to_bot
from models.group_leader_model import GroupLeader
from models.region_leader_model import RegionLeader


class RegionalGroupLeaders(Model):
    """
    Many to many модель отношения Региональный лидер - Лидер ДГ
    """
    id = PrimaryKeyField(null=False)
    regional_leader = ForeignKeyField(RegionLeader, backref='regional_group')
    group_leader = ForeignKeyField(GroupLeader, backref='group_regional')

    class Meta:
        db_table = 'regionals_groups'
        database = connect_to_bot
