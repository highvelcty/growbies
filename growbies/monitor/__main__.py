from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from enum import StrEnum
from pathlib import Path
import sys
from growbies.session import Session
from growbies.utils.paths import RepoPaths

from . import __doc__ as pkg_doc
from .monitor import main

class Param(StrEnum):
    OUTPUT = 'output'
    TAG = 'tag'

parser = ArgumentParser(description=pkg_doc, formatter_class=ArgumentDefaultsHelpFormatter)
parser.add_argument('-o', f'--{Param.OUTPUT}', help=f'Output directory path.',
                    default=Session.DEFAULT_OUTPUT)
parser.add_argument('-t', f'--{Param.TAG}', action='append', help='Session tags')

ns_args = parser.parse_args(sys.argv[1:])
sess = Session(getattr(ns_args, Param.OUTPUT), getattr(ns_args, Param.TAG))
main(sess)
