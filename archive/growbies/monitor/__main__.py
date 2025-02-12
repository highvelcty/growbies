from argparse import ArgumentParser
from enum import StrEnum
from pathlib import Path
import sys
from growbies.session import Session

from . import __doc__ as pkg_doc
from .monitor import main

class Param(StrEnum):
    PATH = 'path'
    TAG = 'tag'

parser = ArgumentParser(description=pkg_doc)
parser.add_argument(f'--{Param.TAG}', action='append', help='Session tags')
parser.add_argument(f'--{Param.PATH}',
                     help='Path to session output to begin or resume.')

ns_args = parser.parse_args(sys.argv[1:])
tags = getattr(ns_args, Param.TAG)
path = getattr(ns_args, Param.PATH)

if path is None:
    if tags is None:
        path_or_tags = []
    else:
        path_or_tags = tags
else:
    path_or_tags = Path(path)

main(Session(path_or_tags))
