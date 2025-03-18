import os
from enum import Enum
from pathlib import Path

from growbies import constants

_REPO_ROOT = Path(__file__).parent.parent.parent.resolve()
if _REPO_ROOT.is_relative_to(os.getcwd()):
    _REPO_ROOT = _REPO_ROOT.relative_to(os.getcwd())


class RepoPaths(Enum):
    # .
    REPO_ROOT = _REPO_ROOT
    DOT_COVERAGE = REPO_ROOT / '.coverage'
    DOT_ENV = REPO_ROOT / '.env'
    MAKE_FILE = REPO_ROOT / 'Makefile'
    README_MD = REPO_ROOT / 'README.md'
    RUN_TESTS_SH = REPO_ROOT / 'run_tests.sh'

    # ./build
    BUILD = REPO_ROOT / 'build'
    BUILD_PATHS_ENV = BUILD / 'paths.env'

    # ./dist
    DIST = REPO_ROOT / 'dist'

    # ./htmlcov
    HTMLCOV = REPO_ROOT / 'htmlcov'
    HTMLCOV_INDEX = HTMLCOV / 'index.html'

    # /output
    OUTPUT = REPO_ROOT / 'output'
    DEFAULT_OUTPUT_DIR = OUTPUT / 'default'
    DEFAULT_LOG = OUTPUT / 'log.log'
    DEFAULT_DATA = DEFAULT_OUTPUT_DIR / 'data.csv'
    FILELOCK = OUTPUT / 'file.lock'

    # /growbies
    GROWBIES = REPO_ROOT / 'growbies'
    GROWBIES_EXEC = GROWBIES / 'exec'
    GROWBIES_HUMAN_INPUT = GROWBIES / 'human_input'
    GROWBIES_MONITOR = GROWBIES / 'monitor'
    GROWBIES_PLOT = GROWBIES / 'plot'
    GROWBIES_SAMPLE = GROWBIES / 'sample'
    GROWBIES_SERVICE = GROWBIES / 'service'

    # /growbies/pkg
    GROWBIES_PKG = GROWBIES / 'pkg'
    GROWBIES_PKG_DEB = GROWBIES_PKG / 'deb'
    GROWBIES_PKG_DEB_DEBIAN = GROWBIES_PKG_DEB / 'debian'


class InstallPaths(Enum):
    VAR_LIB_GROWBIES = Path(f'/var/lib/{constants.APPNAME.lower()}')
    VAR_LIB_GROWBIES_LOCK = VAR_LIB_GROWBIES / 'lock'
    VAR_LIB_GROWBIES_LOCK_Q = VAR_LIB_GROWBIES_LOCK / 'cmd_queue.pkl'
    VAR_LIB_GROWBIES_LOCK_SERVICE = VAR_LIB_GROWBIES_LOCK / 'service.lock'

    USR_LIB_GROWBIES = Path(f'/usr/lib/{constants.APPNAME.lower()}')
    USR_LIB_GROWBIES_VENV = USR_LIB_GROWBIES / 'venv'
    USR_LIB_GROWBIES_VENV_ACTIVATE = USR_LIB_GROWBIES_VENV / 'bin/activate'


class DebianPaths(Enum):
    DEBIAN_ROOT = RepoPaths.GROWBIES_PKG_DEB_DEBIAN.value.relative_to(
        RepoPaths.GROWBIES_PKG_DEB.value)
    DEBIAN_TMP = DEBIAN_ROOT / 'tmp'
    DEBIAN_BASE_PYTHON = 'python3.11'
    DEBIAN_VENV = DEBIAN_ROOT / 'venv'
    DEBIAN_VENV_ACTIVATE = DEBIAN_VENV / 'bin/activate'