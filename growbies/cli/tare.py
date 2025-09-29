from argparse import ArgumentParser

from growbies.cli.common import PositionalParam

class Param:
    INIT = 'init'
    INDEX = 'index'
    VALUE = 'value'

def make_cli(parser: ArgumentParser):
    parser.add_argument(PositionalParam.SERIAL, type=str,
                            help=PositionalParam.get_help_str(PositionalParam.SERIAL))
    parser.add_argument(f'--{Param.INIT}', action='store_true',
                        help='Set to initialize to default values.')
    parser.add_argument(Param.INDEX, nargs="?", type=int, help="Tare index to set")
    parser.add_argument(Param.VALUE, nargs="?", type=float,
                        help="Value to set at index. Input NAN (case insensitive) to omit the "
                             "slot.")
