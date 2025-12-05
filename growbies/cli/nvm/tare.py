from argparse import ArgumentParser

from growbies.device.common import MassUnitsType
from growbies.cli.common import Param as CommonParam

class Param:
    INIT = 'init'
    SLOT = 'slot'
    VALUE = 'value'
    DISPLAY_UNITS = 'display_units'

def make_cli(parser: ArgumentParser):
    parser.add_argument(CommonParam.FUZZY_ID, type=str, help=CommonParam.FUZZY_ID.help)
    parser.add_argument(f'--{Param.INIT}', action='store_true',
                        help='Set to initialize to default values.')
    parser.add_argument(Param.SLOT, nargs="?", type=int, help="Tare slot to set")
    parser.add_argument(f'--{Param.VALUE}', type=float, required=False,
                        help="Value to set for the specified tare slot.")
    parser.add_argument(f'--{Param.DISPLAY_UNITS}', type=int,
                        choices=tuple(x.value for x in MassUnitsType),
                        required=False,
                        help='{' + ','.join([f'{x.value}={x}' for x in MassUnitsType]) + '}',
                        metavar='')
