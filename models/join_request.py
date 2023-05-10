from datetime import datetime

from peewee import Model, PrimaryKeyField, DateTimeField, ForeignKeyField

from models.group_leader import GroupLeader
from models.user import User

from database.db_connection import connect_to_bot


class JoinRequest(Model):
    id = PrimaryKeyField(null=False)
    request_date = DateTimeField(default=datetime.now())
    leader = ForeignKeyField(GroupLeader, backref='leader_group')
    user = ForeignKeyField(User, backref='user')

    class Meta:
        db_table = 'join_requests'
        database = connect_to_bot
