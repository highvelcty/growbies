from argparse import ArgumentParser
from enum import StrEnum
from pathlib import Path
import sys
from growbies.session import Session
from growbies.utils.paths import RepoPaths

from . import __doc__ as pkg_doc
from .monitor import main

class Param(StrEnum):
    PATH = 'path'
    TAG = 'tag'

parser = ArgumentParser(description=pkg_doc)
parser.add_argument(f'--{Param.TAG}', action='append', help='Session tags')

ns_args = parser.parse_args(sys.argv[1:])
tags = getattr(ns_args, Param.TAG)

if tags is None:
    sess = Session()
else:
    for path in RepoPaths.OUTPUT.value.iterdir():
        for tag in tags:
            if tag not in path.name:
                break
        else:
            sess = Session(path)
            break
    else:
        sess = Session(tags)

main(sess)
