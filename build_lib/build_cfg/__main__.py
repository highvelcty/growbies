from argparse import ArgumentParser, RawDescriptionHelpFormatter
import sys

from . import __doc__ as pkg_doc
from . import firmware
from . import gateway
from .common import CMD, Cmd, dispatch, Param


parser = ArgumentParser(description=pkg_doc, formatter_class=RawDescriptionHelpFormatter)
parser_adder = parser.add_subparsers(dest=CMD, required=True)
cmd_parsers = dict()
for cmd in Cmd:
    cmd_parser =  parser_adder.add_parser(cmd, help=Cmd.get_help_str(cmd))
    cmd_parsers[cmd] = cmd_parser

cmd_parsers[Cmd.FIRMWARE].add_argument(f'{Param.MODEL_NUMBER}',
                                       default=firmware.Default.MODEL_NUMBER,
                                       help=Param.get_help_str(Param.MODEL_NUMBER),
                                       nargs='?')

cmd_parsers[Cmd.GATEWAY].add_argument(f'{Param.MODEL_NUMBER}',
                                      default=gateway.Default.MODEL_NUMBER,
                                      help=Param.get_help_str(Param.MODEL_NUMBER),
                                      nargs='?')

ns, args = parser.parse_known_args(sys.argv[1:])

dispatch(getattr(ns, CMD), getattr(ns, Param.MODEL_NUMBER))
