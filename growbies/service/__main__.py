from argparse import ArgumentParser
from enum import StrEnum
from growbies.constants import APPNAME
from growbies.session import Session

from . import __doc__ as pkg_doc
from .service import main

class Param(StrEnum):
    START = 'start'
    STOP = 'stop'

parser = ArgumentParser(description=pkg_doc)
parser.add_argument(Param.START, help=f'Start the {APPNAME} service.')
parser.add_argument(Param.STOP, help=f'Stop the {APPNAME} service.')

main(Session())
