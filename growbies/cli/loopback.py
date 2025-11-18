from argparse import ArgumentParser

from growbies.cli.common import PositionalParam

def make_cli(parser: ArgumentParser):
    parser.add_argument(PositionalParam.SERIAL, type=str, help=PositionalParam.SERIAL.help)