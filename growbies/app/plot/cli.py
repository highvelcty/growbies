from argparse import ArgumentParser
from enum import StrEnum

from growbies.cli.common import BaseParam, Param
from growbies.common.utils import timestamp

class PlotParam(BaseParam):
    TYPE = 'type'
    START_TIME = 'start_time'
    END_TIME = 'end_time'

    @property
    def description(self) -> str:
        if self == self.TYPE:
            return "Plot type."
        elif self == self.START_TIME:
            return 'The start of the time series to plot. '
        elif self == self.END_TIME:
            return f'The end of hte time series to plot.'
        else:
            raise ValueError(f'"{self} is not a valid element')

    @property
    def help(self) -> str:
        return self.description


class PlotType(StrEnum):
    TIME = "time"

    @property
    def description(self) -> str:
        if self == self.TIME:
            return "Plot time series data."

def make_cli() -> ArgumentParser:

    parser = ArgumentParser()

    parser.add_argument(
        PlotParam.TYPE,
        type=PlotType,
        choices=list(PlotType),
        help="Plot type.",
    )

    parser.add_argument(
        Param.FUZZY_ID,
        help=Param.FUZZY_ID.help,
    )

    parser.add_argument(
        f"--{PlotParam.START_TIME.kw_cli_name}",
        default="-7 days",
        type=timestamp.parse_relative_time,
        help=(
            "Start time. "
            "Examples: '-7 days', '-1 hour 5 seconds'. "
            "Default: -7 days."
        ),
    )

    parser.add_argument(
        f"--{PlotParam.END_TIME.kw_cli_name}",
        default="now",
        type=timestamp.parse_relative_time,
        help=(
            "End time. "
            "Examples: 'now', '-5 minutes'. "
            "Default: now."
        ),
    )

    return parser