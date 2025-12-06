from argparse import ArgumentParser

from growbies.cli.common import BaseParam
from growbies.cli.common import Param as CommonParam

class Param(BaseParam):
    INACTIVE = 'inactive'

def make_cli(parser: ArgumentParser):
    parser.add_argument(CommonParam.FUZZY_ID, nargs='?', default=None,
                        help='The partial or full identifier of a calibration session.')

    parser.add_argument(
        f'--{Param.INACTIVE.kw_cli_name}',
        action='store_true',
        default=False,
        help='If set, include inactive calibration sessions.'
    )
