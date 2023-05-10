from peewee import Model, PrimaryKeyField, ForeignKeyField

from models.group import Group
from models.group_leader import GroupLeader

from database.db_connection import connect_to_bot


class LeaderGroups(Model):
    id = PrimaryKeyField(null=False)
    leader = ForeignKeyField(GroupLeader, backref='leader_group')
    group = ForeignKeyField(Group, backref='group_leader')

    class Meta:
        db_table = 'leaders_groups'
        database = connect_to_bot
