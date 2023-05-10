from peewee import Model, PrimaryKeyField, CharField, IntegerField, BooleanField

from database.db_connection import connect_to_bot


class User(Model):
    id = PrimaryKeyField(null=False)
    username = CharField(max_length=255)
    telegram_id = IntegerField(null=True)
    telegram_login = CharField(max_length=255, null=True)
    is_admin = BooleanField(default=False)

    class Meta:
        db_table = 'users'
        database = connect_to_bot
