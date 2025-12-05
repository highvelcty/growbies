from argparse import ArgumentParser

from growbies.cli.common import Param as CommonParam, BaseParam

class Param(BaseParam):
    REF_MASS = 'ref_mass'
    SENSOR_REF_MASS = 'sensor_ref_mass'

def make_cli(parser: ArgumentParser):
    parser.add_argument(CommonParam.FUZZY_ID, nargs='?', default=None,
                        help=CommonParam.FUZZY_ID.help)

    # --- Aggregate reference mass ---
    parser.add_argument(
        f'--{Param.REF_MASS.kw_cli_name}',
        type=float,
        default=None,
        help='Reference mass in grams applied to the entire scale during calibration.'
    )

    # --- Per-sensor reference mass (comma-separated list) ---
    parser.add_argument(
        f'--{Param.SENSOR_REF_MASS.kw_cli_name}',
        type=float,
        nargs='*',
        default=None,
        help=(
            f'Reference mass in grams per sensor (space-separated list). '
            f'Example: --{Param.SENSOR_REF_MASS.kw_cli_name} 100.0 102.1 98.4'
        ),
    )