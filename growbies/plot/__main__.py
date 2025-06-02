from argparse import ArgumentParser
from enum import StrEnum
from pathlib import Path
import sys

from . import __doc__ as pkg_doc
from . import plot
from growbies.session import Session

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
# plot.velo_vs_scale()
# plot.bucket_test(path)
plot.time_plot(path, normalize=False)
# plot.csv_difference(path)
# plot.resister_divider()
# plot.measure_noise(path)

# plot.single_channel(path)