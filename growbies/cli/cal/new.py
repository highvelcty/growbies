from argparse import ArgumentParser

from growbies.cli.common import Param as CommonParam

def make_cli(parser: ArgumentParser):
    parser.add_argument(CommonParam.FUZZY_ID, nargs='?', default=None,
                        help='The partial or full identifier of a device to create a calibration '
                             'session for.')
