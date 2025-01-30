from argparse import ArgumentParser
from enum import StrEnum
from pathlib import Path
import sys

from . import __doc__ as pkg_doc
from . import plot
from growbies import Session

class Param(StrEnum):
    PATH = 'path'

parser = ArgumentParser(description=pkg_doc)
parser.add_argument(f'--{Param.PATH}',
                     help='Path to session output to begin or resume.')

ns_args = parser.parse_args(sys.argv[1:])
path = getattr(ns_args, Param.PATH)

if path is not None:
    path = Path(path)

_ = Session()
plot.csv(path)
# plot.resister_divider()