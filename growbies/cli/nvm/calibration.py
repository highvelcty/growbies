from argparse import ArgumentParser, SUPPRESS

from growbies.cli.common import Param as CommonParam
from growbies.device.common import calibration as cal_mod

class Param:
    INIT = 'init'

def make_cli(parser: ArgumentParser):
    parser.add_argument(CommonParam.FUZZY_ID, nargs='?', default=None,
                        help=CommonParam.FUZZY_ID.help)
    parser.add_argument(f'--{Param.INIT}', action='store_true',
                        help='Set to initialize to default values.')
    klass = cal_mod.SensorCalibration
    parser.add_argument(
        f'--{klass.Field.COEFFS.public_name}',
        action='append',
        default=SUPPRESS,
        metavar='SENSOR_ROW [VALUE ...]',

        nargs='+',
        type=float,
        help = f'Set mass/temperature correction coefficients for a sensor. Each row '
               f'represents a sensor and each column a coefficient. Missing coefficients will '
               f'remain unchanged.')
