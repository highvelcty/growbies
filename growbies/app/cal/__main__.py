import sys

from .cli import Action, make_cli
from growbies.cli.common import Param
from growbies.session import log

log.start()

# Must import after initializing logging
from . import plot
from . import sample

def main(argv=None):
    parser = make_cli()
    args, forward_args = parser.parse_known_args(argv)
    cmd = getattr(args, Param.ACTION)

    if cmd == Action.PLOT:
        plot.execute(args)
    elif cmd == Action.SAMPLE:
        sample.execute(args, forward_args)
    else:
        raise Exception(f'Invalid command: "{cmd}"')

if __name__ == "__main__":
    main(sys.argv[1:])