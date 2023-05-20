import os

from peewee import PostgresqlDatabase
from psycopg2 import connect

connect_to_wolrus_hub = connect(
    host=os.getenv('WOL_DB_HOST'),
    database=os.getenv('WOL_DB_NAME'),
    user=os.getenv('WOL_DB_USER'),
    password=os.getenv('WOL_DB_PASSWORD'),
    port=os.getenv('WOL_DB_PORT')
)

connect_to_bot = PostgresqlDatabase(
    os.getenv('DB_NAME'),
    host=os.getenv('DB_HOST'),
    port=os.getenv('DB_PORT'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    autoconnect=False
)
