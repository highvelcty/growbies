import argparse
from argparse import ArgumentParser

from growbies.cli.common import internal_to_external_field, PositionalParam
from growbies.device.common import calibration as cal_mod

class Param:
    INIT = 'init'

def make_cli(parser: ArgumentParser):
    parser.add_argument(PositionalParam.SERIAL, type=str,
                            help=PositionalParam.get_help_str(PositionalParam.SERIAL))
    parser.add_argument(f'--{Param.INIT}', action='store_true',
                        help='Set to initialize to default values.')
    klass = cal_mod.SensorCalibration
    parser.add_argument(
        f'--{internal_to_external_field(klass.Field.COEFFS)}',
        action='append',
        default=argparse.SUPPRESS,
        metavar='SENSOR_ROW [VALUE ...]',

        nargs='+',
        type=float,
        help = f'Set mass/temperature correction coefficients for a sensor. Each row '
               f'represents a sensor and each column a coefficient. Missing coefficients will '
               f'remain unchanged.')
