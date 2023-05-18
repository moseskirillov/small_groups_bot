from peewee import Model, PrimaryKeyField, ForeignKeyField

from database.db_connection import connect_to_bot
from models.group_leader_model import GroupLeader
from models.group_model import Group


class LeaderGroups(Model):
    """
    Many to many модель отношения Лидер - ДГ
    """
    id = PrimaryKeyField(null=False)
    leader = ForeignKeyField(GroupLeader, backref='leader_group')
    group = ForeignKeyField(Group, backref='group_leader')

    class Meta:
        db_table = 'leaders_groups'
        database = connect_to_bot
