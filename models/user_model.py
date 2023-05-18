from peewee import Model, PrimaryKeyField, CharField, BooleanField, BigIntegerField

from database.db_connection import connect_to_bot


class User(Model):
    """
    Модель пользователя бота
    """
    id = PrimaryKeyField(null=False)
    user_id = BigIntegerField(null=True)
    first_name = CharField(max_length=255, null=True)
    last_name = CharField(max_length=255, null=True)
    phone_number = CharField(max_length=255, null=True)
    telegram_login = CharField(max_length=255, null=True)
    is_admin = BooleanField(default=False)

    class Meta:
        db_table = 'users'
        database = connect_to_bot
