from argparse import ArgumentParser, RawDescriptionHelpFormatter
from enum import StrEnum
from growbies.cli.common import BaseParam, Param


DEFAULT_MASS_CAL_SAMPLES = 25
DEFAULT_TEMP_CAL_SAMPLES = 3
DEFAULT_TEMP_CAL_INTERVAL_SEC = 10.0

class Action(StrEnum):
    PLOT = 'plot'
    SAMPLE = 'sample'

    @property
    def description(self) -> str:
        if self == self.PLOT:
            return 'Plot data.'
        elif self == self.SAMPLE:
            return 'Sample data.'
        else:
            return 'Invalid command'

    @property
    def help(self) -> str:
        return self.description

class PlotAction(StrEnum):
    MASS = "mass"
    TEMP = "temp"
    TIME = 'time'


    @property
    def description(self) -> str:
        return {
            self.MASS: "Plot mass calibration.",
            self.TEMP: "Plot temperature calibration.",
            self.TIME: "Plot mass & temperature over time"
        }[self]

    @property
    def help(self) -> str:
        return self.description

class SampleAction(StrEnum):
    MASS = "mass"
    TEMP = "temp"

    @property
    def description(self) -> str:
        return {
            self.MASS: "Sample for mass calibration.",
            self.TEMP: "Sample for thermal calibration.",
        }[self]

    @property
    def help(self) -> str:
        return self.description

class MassSampleParam(BaseParam):
    COUNT = 'count'

class TempSSampleParam(BaseParam):
    INTERVAL = 'interval'

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

    sample_parser = actions.add_parser(
        Action.SAMPLE,
        help=Action.SAMPLE.help,
        description=Action.SAMPLE.description,
    )

    sample_types = sample_parser.add_subparsers(
        dest=Action.SAMPLE,
        required=True,
        title=Action.SAMPLE,
        description="The type of sample.",
    )

    for sample_action in SampleAction:
        p = sample_types.add_parser(
            sample_action.value,
            help=sample_action.help,
            description=sample_action.description,
        )

        if sample_action == SampleAction.MASS:
            p.add_argument(
                f'--{MassSampleParam.COUNT.kw_cli_name}',
                type=int,
                default=DEFAULT_MASS_CAL_SAMPLES,
                help=f'Number of samples to collect (default: {DEFAULT_MASS_CAL_SAMPLES}).',
            )
        elif sample_action == SampleAction.TEMP:
            p.add_argument(
                f'--{MassSampleParam.COUNT.kw_cli_name}',
                type=int,
                default=DEFAULT_TEMP_CAL_SAMPLES,
                help=f'Number of samples to collect (default: {DEFAULT_TEMP_CAL_SAMPLES}).',
            )

            p.add_argument(
                f'--{TempSSampleParam.INTERVAL.kw_cli_name}',
                type=float,
                default=DEFAULT_TEMP_CAL_INTERVAL_SEC,
                help=f'Interval (default: {DEFAULT_TEMP_CAL_INTERVAL_SEC}).',
            )

    return parser
