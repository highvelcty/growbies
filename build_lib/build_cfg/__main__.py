from argparse import ArgumentParser, RawDescriptionHelpFormatter
import sys

from . import __doc__ as pkg_doc
from .common import CMD, Cmd, dispatch


parser = ArgumentParser(description=pkg_doc, formatter_class=RawDescriptionHelpFormatter)
parser_adder = parser.add_subparsers(dest=CMD, required=True)
cmd_parsers = dict()
for cmd in Cmd:
    cmd_parser =  parser_adder.add_parser(cmd, help=Cmd.get_help_str(cmd))
    cmd_parsers[cmd] = cmd_parser

ns, args = parser.parse_known_args(sys.argv[1:])

dispatch(getattr(ns, CMD))
