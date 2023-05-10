from peewee import Model, PrimaryKeyField, CharField, TimeField, ForeignKeyField

from models.group_leader import GroupLeader

from database.db_connection import connect_to_bot


class Group(Model):
    id = PrimaryKeyField(null=False)
    metro = CharField(max_length=50)
    day = CharField(max_length=50)
    time = TimeField()
    age = CharField(max_length=50)
    type = CharField(max_length=50)
    leader = ForeignKeyField(GroupLeader, backref='leader')

    class Meta:
        db_table = 'groups'
        database = connect_to_bot
