from . import constants
import psycopg2

def init_tables():
    conn = psycopg2.connect(f'dbname={constants.DB_NAME} user={constants.DB_USER}')