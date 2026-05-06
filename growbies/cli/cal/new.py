from argparse import ArgumentParser

from growbies.cli.common import BaseParam
from growbies.app.cal import DefaultCalSessionName

class Param(BaseParam):
    SESSION_NAME = 'session_name'

    @property
    def help(self):
        if self == self.SESSION_NAME:
            return (f'The name of the session to be created. The default is to increment past the '
                    f'highest value past this format string: "{DefaultCalSessionName.FMT}".')

def make_cli(parser: ArgumentParser):

    parser.add_argument(f'--{Param.SESSION_NAME.kw_cli_name}', nargs='?', default=None,
                        help=Param.SESSION_NAME.help)
