from argparse import ArgumentParser
from enum import StrEnum

from growbies.cli.common import Param as CommonParam

class Param(StrEnum):
    REF_MASS = 'ref-mass'
    SENSOR_REF_MASS = 'sensor-ref-mass'

    @property
    def py_name(self):
        return self.value.replace('-', '_')

def make_cli(parser: ArgumentParser):
    parser.add_argument(CommonParam.FUZZY_ID, nargs='?', default=None,
                        help=CommonParam.FUZZY_ID.help)

    # --- Aggregate reference mass ---
    parser.add_argument(
        f'--{Param.REF_MASS}',
        type=float,
        default=None,
        help="Reference mass in grams  applied to the entire scale during calibration."
    )

    # --- Per-sensor reference mass (comma-separated list) ---
    parser.add_argument(
        f'--{Param.SENSOR_REF_MASS}',
        type=float,
        nargs='*',
        default=None,
        help=(
            f'Reference mass in grams per sensor (space-separated list). '
            f'Example: --{Param.SENSOR_REF_MASS} 100.0 102.1 98.4'
        ),
    )