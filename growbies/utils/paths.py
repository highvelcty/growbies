import os
from enum import Enum
from pathlib import Path

from growbies import constants

_REPO_ROOT = Path(__file__).parent.parent.parent.resolve()
if _REPO_ROOT.is_relative_to(os.getcwd()):
    _REPO_ROOT = _REPO_ROOT.relative_to(os.getcwd())


class RepoPaths(Enum):
    # .
    ROOT = _REPO_ROOT
    DOT_COVERAGE = ROOT / '.coverage'
    DOT_ENV = ROOT / '.env'
    MAKE_FILE = ROOT / 'Makefile'
    README_MD = ROOT / 'README.md'
    RUN_TESTS_SH = ROOT / 'run_tests.sh'

    # ./build
    BUILD = ROOT / 'build'
    BUILD_PATHS_ENV = BUILD / 'paths.env'

    # ./dist
    DIST = ROOT / 'dist'

    # ./htmlcov
    HTMLCOV = ROOT / 'htmlcov'
    HTMLCOV_INDEX = HTMLCOV / 'index.html'

    # /output
    OUTPUT = ROOT / 'output'
    DEFAULT_OUTPUT_DIR = OUTPUT / 'default'
    DEFAULT_LOG = OUTPUT / 'log.log'
    DEFAULT_DATA = DEFAULT_OUTPUT_DIR / 'data.csv'
    FILELOCK = OUTPUT / 'file.lock'

    # /growbies
    GROWBIES = ROOT / 'growbies'
    GROWBIES_EXEC = GROWBIES / 'exec'
    GROWBIES_HUMAN_INPUT = GROWBIES / 'human_input'
    GROWBIES_MONITOR = GROWBIES / 'monitor'
    GROWBIES_PLOT = GROWBIES / 'plot'
    GROWBIES_SAMPLE = GROWBIES / 'sample'
    GROWBIES_SERVICE = GROWBIES / 'service'


class InstallPaths(Enum):
    VAR_LIB_GROWBIES = Path(f'/var/lib/{constants.APPNAME.lower()}')
    VAR_LIB_GROWBIES_LOCK = VAR_LIB_GROWBIES / 'lock'
    VAR_LIB_GROWBIES_LOCK_Q = VAR_LIB_GROWBIES_LOCK / 'cmd_queue.pkl'
    VAR_LIB_GROWBIES_LOCK_SERVICE = VAR_LIB_GROWBIES_LOCK / 'service.lock'
