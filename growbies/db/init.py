from .init_db_and_user import init_db_and_user
from .init_tables import init_tables

def main():
    init_db_and_user()
    init_tables()

