from argparse import ArgumentParser, RawDescriptionHelpFormatter
from enum import StrEnum
import logging

from growbies.cli.common import Param

STDIN_LEVEL = logging.INFO + 1
STDOUT_LEVEL = logging.INFO + 2
STDERR_LEVEL = logging.ERROR + 1

logging.addLevelName(STDIN_LEVEL, "STDIN")
logging.addLevelName(STDOUT_LEVEL, "STDOUT")
logging.addLevelName(STDERR_LEVEL, "STDERR")

class Action(StrEnum):
    PLOT = "plot"

    @property
    def description(self) -> str:
        return "Plot data."

    @property
    def help(self) -> str:
        return self.description


class PlotAction(StrEnum):
    MASS = "mass"
    TEMP = "temp"

    @property
    def description(self) -> str:
        return {
            self.MASS: "Plot mass calibration.",
            self.TEMP: "Plot temperature calibration.",
        }[self]

    @property
    def help(self) -> str:
        return self.description


def make_cli() -> ArgumentParser:
    parser = ArgumentParser(
        formatter_class=RawDescriptionHelpFormatter,
    )

    actions = parser.add_subparsers(
        dest=Param.ACTION,
        required=True,
        help=Param.ACTION.help,
    )

    plot_parser = actions.add_parser(
        Action.PLOT,
        help=Action.PLOT.help,
        description=Action.PLOT.description,
    )

    plot_types = plot_parser.add_subparsers(
        dest=Action.PLOT,
        required=True,
        title=Action.PLOT,
        description="The type of plot.",
    )

    for plot_action in PlotAction:
        p = plot_types.add_parser(
            plot_action.value,
            help=plot_action.help,
            description=plot_action.description,
        )

        p.add_argument(
            Param.FUZZY_ID,
            help=Param.FUZZY_ID.help,
        )

    return parser