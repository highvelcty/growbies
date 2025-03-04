from argparse import ArgumentParser
from enum import StrEnum

from . import __doc__ as pkg_doc
from .sample import main
from growbies.utils.paths import Paths
from growbies import Session

class Param(StrEnum):
    TAG = 'tag'

parser = ArgumentParser(description=pkg_doc)
parser.add_argument(f'--{Param.TAG}', action='append', help='Session tags')

ns_args = parser.parse_args()
tags = getattr(ns_args, Param.TAG)

if tags is None:
    parser.error('Tag parameter must not be None.')

for path in Paths.OUTPUT.value.iterdir():
    found_tags = list()
    for tag in tags:
        if tag in path.name:
            found_tags.append(True)
        else:
            found_tags.append(False)
    if all(found_tags):
        sess = Session(path)
        break
else:
    sess = Session(tags)

main(sess)
