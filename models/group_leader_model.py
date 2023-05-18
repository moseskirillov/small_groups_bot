"""
Модельный класс
"""

from peewee import Model, PrimaryKeyField, CharField, BigIntegerField

from database.db_connection import connect_to_bot


class GroupLeader(Model):
    """
    Модель лидера ДГ
    """
    id = PrimaryKeyField(null=False)
    name = CharField(max_length=255)
    telegram = CharField(max_length=100, null=True)
    telegram_id = BigIntegerField(null=True)

    class Meta:
        db_table = 'group_leaders'
        database = connect_to_bot
