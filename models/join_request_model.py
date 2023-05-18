from datetime import datetime

from peewee import Model, PrimaryKeyField, DateTimeField, ForeignKeyField

from database.db_connection import connect_to_bot
from models.group_leader_model import GroupLeader
from models.user_model import User


class JoinRequest(Model):
    """
    Модель запроса на присоединение к ДГ
    """
    id = PrimaryKeyField(null=False)
    request_date = DateTimeField(default=datetime.now())
    leader = ForeignKeyField(GroupLeader, backref='leader_group')
    user = ForeignKeyField(User, backref='user')

    class Meta:
        db_table = 'join_requests'
        database = connect_to_bot
