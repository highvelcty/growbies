from argparse import ArgumentParser
from enum import StrEnum

from growbies.cli.common import BaseParam, Param


class PlotParam(BaseParam):
    TYPE = 'type'

    @property
    def description(self) -> str:
        if self == self.TYPE:
            return "Plot type."

    @property
    def help(self) -> str:
        return self.description


class PlotType(StrEnum):
    TIME = "time"

    @property
    def description(self) -> str:
        if self == self.TIME:
            return "Plot time series data."
        return "Invalid plot type"


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

    return parser