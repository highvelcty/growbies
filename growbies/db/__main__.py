from argparse import ArgumentParser, RawTextHelpFormatter
from enum import StrEnum
import sys

from . import __doc__ as pkg_doc
from .init_db_and_user import init_db_and_user
from growbies.cli.common import CMD
from growbies.db.engine import get_db_engine
from growbies.constants import APPNAME, USERNAME

class Param:
    KEEP_PRIVILEGES = 'keep_privileges'

class SubCmd(StrEnum):
    INIT_DB_AND_USER = 'init_db_and_user'
    INIT_TABLES = 'init_tables'

    @classmethod
    def get_help_str(cls, sub_cmd_: 'SubCmd') -> str:
        if sub_cmd_ == cls.INIT_DB_AND_USER:
            return f'Initialize the {APPNAME} database.'
        elif sub_cmd_ == cls.INIT_TABLES:
            return f'Initialize tables for {APPNAME} database.'
        else:
            raise ValueError(f'Database sub-command "{sub_cmd_}" does not exist')

parser = ArgumentParser(description=pkg_doc, formatter_class=RawTextHelpFormatter)
sub = parser.add_subparsers(dest=CMD, required=True)
for sub_cmd in SubCmd:
    sub.add_parser(sub_cmd, help=SubCmd.get_help_str(sub_cmd), add_help=False)

parser.add_argument(f'--{Param.KEEP_PRIVILEGES}', default=False, action='store_true',
                    help=f'By default, if the program is executed with root privileges, these will '
                         f'be dropped by switching to the "{USERNAME}" user. This is typically '
                         f'only se to to False during package installation work.')

ns_dict = vars(parser.parse_args(sys.argv[1:]))
sub_cmd = ns_dict[CMD]

if SubCmd.INIT_DB_AND_USER == sub_cmd:
    init_db_and_user()
elif SubCmd.INIT_TABLES == sub_cmd:
    get_db_engine()
