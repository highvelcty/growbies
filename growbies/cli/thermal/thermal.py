from argparse import ArgumentParser, SUPPRESS, ArgumentTypeError

from growbies.cli.common import BaseParam, Param
from growbies.common.enum import ThermalDeviceMode

__all__ = ['make_cli', 'ModParam']


class ModParam(BaseParam):
    ACTIVATE = 'activate'
    DEACTIVATE = 'deactivate'
    MODE = 'mode'
    DUTY_CYCLE = 'duty_cycle'
    SET_POINT = 'set_point'

    @property
    def help(self) -> str:
        if self == self.ACTIVATE:
            return 'Activate the thermal device.'
        elif self == self.DEACTIVATE:
            return 'Deactivate the thermal device.'
        elif self == self.MODE:
            return (
                f'The control mode. '
                f'{ThermalDeviceMode.AUTO.name} regulates temperature automatically. '
                f'{ThermalDeviceMode.MANUAL.name} applies the requested duty cycle.'
            )
        elif self == self.DUTY_CYCLE:
            return 'Output duty cycle, in percent.'
        elif self == self.SET_POINT:
            return 'Temperature set point in degrees Celsius.'
        return ''


def make_cli(parser: ArgumentParser):

    parser.add_argument(
        Param.FUZZY_ID,
        nargs='?',
        default=None,
        help=Param.FUZZY_ID.help,
    )

    activate_group = parser.add_mutually_exclusive_group()

    activate_group.add_argument(
        f'--{ModParam.ACTIVATE}',
        dest=ModParam.ACTIVATE,
        action='store_true',
        default=SUPPRESS,
        help=ModParam.ACTIVATE.help,
    )

    activate_group.add_argument(
        f'--{ModParam.DEACTIVATE}',
        dest=ModParam.ACTIVATE,
        action='store_false',
        default=SUPPRESS,
        help=ModParam.DEACTIVATE.help,
    )

    parser.add_argument(
        f'--{ModParam.MODE}',
        type=int,
        choices=list(ThermalDeviceMode),
        default=SUPPRESS,
        help=ModParam.MODE.help,
    )

    parser.add_argument(
        f'--{ModParam.DUTY_CYCLE.kw_cli_name}',
        type=_duty_cycle_type,
        default=SUPPRESS,
        help=ModParam.DUTY_CYCLE.help,
    )

    parser.add_argument(
        f'--{ModParam.SET_POINT.kw_cli_name}',
        type=float,
        default=SUPPRESS,
        help=ModParam.SET_POINT.help,
    )


def _duty_cycle_type(value: str) -> float:
    try:
        value = float(value)
    except ValueError:
        raise ArgumentTypeError("Duty cycle must be a number.")

    if not (0.0 <= value <= 100.0):
        raise ArgumentTypeError(
            "Duty cycle must be between 0 and 100 percent, inclusive."
        )

    return value