from argparse import ArgumentParser

from growbies.cli.common import Param as CommonParam
from growbies.device.cmd import ReadDeviceCmd

class Param:
    TIMES = 'times'
    RAW = 'raw'

def make_cli(parser: ArgumentParser):
    parser.add_argument(CommonParam.FUZZY_ID, nargs='?', default=None,
                        help=CommonParam.FUZZY_ID.help)
    parser.add_argument(f'--{Param.TIMES}', type=int, nargs='?',
                        default=ReadDeviceCmd.DEFAULT_TIMES,
                        help='The number of samples to take for the read operations')
    parser.add_argument(f'--{Param.RAW}', action='store_true',
                        help='Read raw, uncorrected/calibrated values.')
