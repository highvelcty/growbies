from argparse import ArgumentParser

from growbies.cli.common import Param as CommonParam, BaseParam

class Param(BaseParam):
    REF_MASS = 'ref_mass'
    RESET = 'reset'
    SENSOR_REF_MASS = 'sensor_ref_mass'

def add_only(expr: str) -> float:
    return sum(float(val) for val in expr.split('+'))

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

    parser.add_argument(f'--{Param.RESET.kw_cli_name}', dest=Param.RESET.kw_cli_name,
                        action='store_true',
                        help='Reset the filters prior to reading.')

    # --- Per-sensor reference mass (comma-separated list) ---
    parser.add_argument(
        f'--{Param.SENSOR_REF_MASS.kw_cli_name}',
        type=add_only,
        nargs='*',
        default=None,
        help=(
            f'Reference mass in grams per sensor (space-separated list). '
            f'Example: --{Param.SENSOR_REF_MASS.kw_cli_name} 100.0 102.1 98.4'
        ),
    )