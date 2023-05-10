from peewee import Model, PrimaryKeyField, ForeignKeyField

from models.group_leader import GroupLeader
from models.region_leader import RegionLeader

from database.db_connection import connect_to_bot


class RegionalGroupLeaders(Model):
    id = PrimaryKeyField(null=False)
    regional_leader = ForeignKeyField(RegionLeader, backref='regional_group')
    group_leader = ForeignKeyField(GroupLeader, backref='group_regional')

    class Meta:
        db_table = 'regionals_groups'
        database = connect_to_bot
