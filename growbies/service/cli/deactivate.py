from argparse import ArgumentParser

from .common import PositionalParam


def make(parser: ArgumentParser):
    parser.add_argument(PositionalParam.SERIALS, nargs='+', type=str,
                        help=PositionalParam.get_help_str(PositionalParam.SERIALS))
