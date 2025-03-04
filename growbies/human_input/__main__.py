from argparse import ArgumentParser
from enum import StrEnum

from . import __doc__ as pkg_doc
from .human_input import main
from growbies import Session

class Param(StrEnum):
    PATH = 'path'

parser = ArgumentParser(description=pkg_doc)
parser.add_argument(Param.PATH,
                    help='Path to session output to begin or resume.')

ns_args = parser.parse_args()

path = getattr(ns_args, Param.PATH)
main(Session(path))
