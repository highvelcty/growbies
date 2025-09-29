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
    parser.add_argument(
        f'--{internal_to_external_field(cal_mod.Calibration.Field.MASS_TEMP_COEFF)}',
        action='append',
        default=argparse.SUPPRESS,
        metavar=('SENSOR_ROW', ) + (('VALUE',) * cal_mod.Calibration.COEFF_COUNT),
        nargs=cal_mod.Calibration.COEFF_COUNT + 1,
        type=float,
        help = f'Set mass/temperature correction coefficients for a sensor. Each row '
               f'represents a sensor and each column a coefficient. The matrix '
               f'dimensions are '
               f'[{cal_mod.Calibration.MASS_SENSOR_COUNT}][{cal_mod.Calibration.COEFF_COUNT}].')
    parser.add_argument(
        f'--{internal_to_external_field(cal_mod.Calibration.Field.MASS_COEFF)}',
        default=argparse.SUPPRESS,
        nargs = cal_mod.Calibration.COEFF_COUNT,
        type=float,
        help = f'Set mass calibration coefficients. There are '
               f'{cal_mod.Calibration.COEFF_COUNT} coefficients.')
