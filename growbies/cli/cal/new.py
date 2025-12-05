from argparse import ArgumentParser

from growbies.cli.common import Param as CommonParam, BaseParam
from growbies.app.cal import DefaultCalSessionName

class Param(BaseParam):
    SESSION_NAME = 'session_name'

    @property
    def help(self):
        if self == self.SESSION_NAME:
            return (f'The name of the session to be created. The default is to increment past the '
                    f'highest value past this format string: "{DefaultCalSessionName.FMT}".')
        return f'Unimplemented help for parameter "{self}"'

def make_cli(parser: ArgumentParser):
    parser.add_argument(CommonParam.FUZZY_ID,
                        help='The partial or full identifier of a device to create a calibration '
                             'session for.')
    parser.add_argument(f'--{Param.SESSION_NAME.kw_cli_name}', nargs='?', default=None,
                        help=Param.SESSION_NAME.help)
