from argparse import ArgumentParser, RawTextHelpFormatter
import os
import shlex
import sys

from . import __doc__ as pkg_doc
from . import cfg, db, device, exec, human_input, monitor, plot, sample, service


CMD = 'cmd'

parser = ArgumentParser(description=pkg_doc,
                        formatter_class=RawTextHelpFormatter)
sub = parser.add_subparsers(dest=CMD, required=True)

for pkg in (cfg, db, device,  exec, human_input, monitor, plot, sample, service):
    sub.add_parser(pkg.__name__.split('.')[-1], help=pkg.__doc__, add_help=False)

ns, args = parser.parse_known_args(sys.argv[1:])
sub_cmd = shlex.split(f'{sys.executable} -m {__package__}.{getattr(ns, CMD)} ') + sys.argv[2:]
os.execvp(sys.executable, sub_cmd)
