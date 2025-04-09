from . import constants

import psycopg2
from psycopg2.extensions import connection

from growbies.utils.paths import RepoPaths

def _create_tables(conn: connection):
    with conn.cursor() as cursor:
        with open(RepoPaths.GROWBIES_DB_SQL_INIT_TABLES.value, 'r') as inf:
            cursor.execute(inf.read())
        conn.commit()

def init_tables():
    conn = psycopg2.connect(f'dbname={constants.DB_NAME} user={constants.DB_USER}')

    _create_tables(conn)

    conn.close()
