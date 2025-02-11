from argparse import ArgumentParser

from . import __doc__ as pkg_doc
from .execute import main
from growbies import Session

parser = ArgumentParser(description=pkg_doc)
parser.parse_args()

_ = Session()
main()
