from sqlmodel import create_engine, SQLModel
import psycopg2
from psycopg2.extensions import connection

from . import constants
from growbies.utils.paths import RepoPaths

def _create_tables(conn: connection):
    with conn.cursor() as cursor:
        with open(RepoPaths.abs(RepoPaths.GROWBIES_DB_SQL_INIT_TABLES), 'r') as inf:
            cursor.execute(inf.read())
        conn.commit()

def init_tables():
    # All SQLModels with table=True metadata will be created as tables in the database
    # from growbies.db import models
    # engine = create_engine(constants.SQLMODEL_LOCAL_ADDRESS, echo_pool=True)
    # SQLModel.metadata.create_all(engine)

    conn = psycopg2.connect(f'dbname={constants.DB_NAME} user={constants.DB_USER}')

    _create_tables(conn)

    conn.close()

