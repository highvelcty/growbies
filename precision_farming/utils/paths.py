import os
from enum import Enum
from pathlib import Path

_ROOT = Path(__file__).parent.parent.parent.resolve()
if _ROOT.is_relative_to(os.getcwd()):
    _ROOT = _ROOT.relative_to(os.getcwd())


class Paths(Enum):
    # /
    ROOT = _ROOT
    DOT_COVERAGE = ROOT / '.coverage'
    DOT_ENV = ROOT / '.env'
    MAKE_FILE = ROOT / 'Makefile'
    README_MD = ROOT / 'README.md'
    RUN_TESTS_SH = ROOT / 'run_tests.sh'

    # /build
    BUILD = ROOT / 'build'
    BUILD_PATHS_ENV = BUILD / 'paths.env'

    # /dist
    DIST = ROOT / 'dist'

    # /htmlcov
    HTMLCOV = ROOT / 'htmlcov'
    HTMLCOV_INDEX = HTMLCOV / 'index.html'

    # /precision_farming
    PRECISION_FARMING = ROOT / 'precision_farming'

    # /venv
    VENV = ROOT / 'venv'

    # /venv/bin
    VENV_BIN = VENV / 'bin'
    VENV_BIN_ACTIVATE = VENV_BIN / 'activate'

    # /venv/extras
    VENV_EXTRAS = VENV / 'extras'
    VENV_EXTRAS_BUILD = VENV_EXTRAS / 'BUILD'
    VENV_EXTRAS_TESTS = VENV_EXTRAS / 'TESTS'
