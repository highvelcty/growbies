from growbies.constants import APPNAME

RDBMS_SERVICE = 'postgresql'
DB_NAME = APPNAME.lower()
DB_USER = APPNAME.lower()
ADMIN_DB_USER = 'postgres'
SQLMODEL_LOCAL_ADDRESS = f'postgresql+psycopg2://{DB_USER}@localhost/{DB_NAME}'
