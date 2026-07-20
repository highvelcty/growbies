import sys

from .cli import make_cli, PlotParam, PlotType
from growbies.cli.common import Param
from growbies.session import log

log.start()

# Must import after initializing logging
from . import time_series

def main(argv=None):
    parser = make_cli()
    args, forward_args = parser.parse_known_args(argv)
    plot_type = getattr(args, PlotParam.TYPE)
    fuzzy_id = getattr(args, Param.FUZZY_ID)

    if plot_type == PlotType.TIME:
        time_series.plot_time_series(fuzzy_id)
    else:
        raise TypeError(f'Invalid plotting type: "{plot_type}"')

if __name__ == "__main__":
    main(sys.argv[1:])