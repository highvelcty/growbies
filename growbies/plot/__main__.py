from argparse import ArgumentParser

from . import __doc__ as pkg_doc
from . import plot
from growbies import Session


parser = ArgumentParser(description=pkg_doc)
parser.parse_args()

_ = Session()
plot.csv()
# plot.resister_divider()