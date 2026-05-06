import logging
import sys

from .cli import Action, make_cli
from growbies.cli.common import Param
from growbies.session import log

PATH_TO_LOG = '/tmp/growbies.log'
log.start(PATH_TO_LOG)

# Must import after initializing logging
from . import finalize

def main(argv=None):
    parser = make_cli()
    args = parser.parse_args(argv)
    cmd = getattr(args, Param.ACTION)

    if cmd == Action.FINALIZE:
        finalize.execute(args)

if __name__ == "__main__":
    main(sys.argv[1:])