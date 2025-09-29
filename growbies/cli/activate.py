from argparse import ArgumentParser

from growbies.cli.common import PositionalParam

def make_cli(parser: ArgumentParser):
    parser.add_argument(PositionalParam.SERIALS, nargs='+', type=str,
                        help=PositionalParam.get_help_str(PositionalParam.SERIALS))
