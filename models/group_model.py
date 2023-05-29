from peewee import Model, PrimaryKeyField, CharField, TimeField, ForeignKeyField, BooleanField

from database.db_connection import connect_to_bot
from models.group_leader_model import GroupLeader


class Group(Model):
    """
    Модель ДГ
    """
    id = PrimaryKeyField(null=False)
    metro = CharField(max_length=50)
    day = CharField(max_length=50)
    time = TimeField()
    age = CharField(max_length=50)
    type = CharField(max_length=50)
    is_open = BooleanField(default=True)
    leader = ForeignKeyField(GroupLeader, backref='leader')

    class Meta:
        db_table = 'groups'
        database = connect_to_bot
