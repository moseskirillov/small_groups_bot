from peewee import Model, PrimaryKeyField, CharField, IntegerField

from database.db_connection import connect_to_bot


class RegionLeader(Model):
    id = PrimaryKeyField(null=False)
    name = CharField(max_length=255)
    telegram = CharField(max_length=100)
    telegram_id = IntegerField(null=True)

    class Meta:
        db_table = 'regional_leaders'
        database = connect_to_bot
