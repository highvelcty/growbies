from enum import Enum
from pathlib import Path
import os

from growbies import constants
from growbies.utils import subprocess_utils
from growbies.utils.environment import Environment


_REPO_ROOT = os.environ.get(Environment.REPO_ROOT)

if _REPO_ROOT is None:
    _REPO_ROOT = subprocess_utils.get_git_repo_root()
else:
    _REPO_ROOT = Path(_REPO_ROOT)

class RepoPaths(Enum):
    # .
    REPO_ROOT = _REPO_ROOT
    DOT_COVERAGE = REPO_ROOT / '.coverage'

    # ./build
    BUILD = REPO_ROOT / 'build'
    BUILD_PATHS_ENV = BUILD / 'paths.env'

    # ./dist
    DIST = REPO_ROOT / 'dist'

    # ./htmlcov
    HTMLCOV = REPO_ROOT / 'htmlcov'
    HTMLCOV_INDEX = HTMLCOV / 'index.html'

    # ./.idea
    DOT_IDEA = REPO_ROOT / '.idea'

    # ./output
    OUTPUT = REPO_ROOT / 'output'
    DEFAULT_OUTPUT_DIR = OUTPUT / 'default'
    DEFAULT_LOG = OUTPUT / 'log.log'
    DEFAULT_DATA = DEFAULT_OUTPUT_DIR / 'data.csv'
    FILELOCK = OUTPUT / 'file.lock'

    # ./growbies
    GROWBIES = REPO_ROOT / 'growbies'
    GROWBIES_EXEC = GROWBIES / 'exec'
    GROWBIES_HUMAN_INPUT = GROWBIES / 'human_input'
    GROWBIES_MONITOR = GROWBIES / 'monitor'
    GROWBIES_PLOT = GROWBIES / 'plot'
    GROWBIES_SAMPLE = GROWBIES / 'sample'
    GROWBIES_SERVICE = GROWBIES / 'service'

    # ./pkg
    PKG = REPO_ROOT / 'pkg'
    PKG_BASH_SRC = PKG / 'bash_src'
    PKG_BASH_SRC_GROWBIES = PKG_BASH_SRC / 'growbies'
    PKG_BASH_SRC_INIT_SH = PKG_BASH_SRC / 'init.sh'
    PKG_DEB = PKG / 'deb'
    PKG_DEB_DEBIAN = PKG_DEB / 'debian'


class InstallPaths(Enum):
    # /usr/lib
    USR_LIB = Path('/usr/lib')
    USR_LIB_GROWBIES = USR_LIB / constants.APPNAME.lower()
    USR_LIB_GROWBIES_VENV = USR_LIB_GROWBIES / 'venv'
    USR_LIB_GROWBIES_VENV_ACTIVATE = USR_LIB_GROWBIES_VENV / 'bin/activate'

    # /usr/bin
    USR_BIN = Path(f'/usr/bin')

    # /var/lib
    VAR_LIB = Path('/var/lib')
    VAR_LIB_GROWBIES = VAR_LIB / constants.APPNAME.lower()

    # /var/opt/lock
    VAR_LIB_GROWBIES_LOCK = VAR_LIB_GROWBIES / 'lock'
    VAR_LIB_GROWBIES_LOCK_Q = VAR_LIB_GROWBIES_LOCK / 'cmd_queue.pkl'
    VAR_LIB_GROWBIES_LOCK_SERVICE = VAR_LIB_GROWBIES_LOCK / 'service.lock'


class DebianPaths(Enum):
    # .
    DEBIAN_ROOT = RepoPaths.PKG_DEB_DEBIAN.value
    DEBIAN_BUILD_SH = DEBIAN_ROOT / 'build.sh'
    DEBIAN_INSTALL_SH = DEBIAN_ROOT / 'install.sh'
    DEBIAN_SRC = DEBIAN_ROOT / 'src'
    DEBIAN_SOURCE_TAR = DEBIAN_ROOT / 'source.tar'

    # ./tmp
    DEBIAN_TMP = DEBIAN_ROOT / 'tmp'
    DEBIAN_TMP_BUILD_PATHS_ENV = DEBIAN_TMP / 'build/paths.env'
    DEBIAN_TMP_USR_LIB_GROWBIES = DEBIAN_TMP / 'opt/growbies'
    DEBIAN_TMP_USR_BIN_GROWBIES = DEBIAN_TMP / 'usr/local/bin'

    # ./venv
    DEBIAN_VENV = DEBIAN_ROOT / 'venv'
    DEBIAN_VENV_ACTIVATE = DEBIAN_VENV / 'bin/activate'

    # command
    DEBIAN_BASE_PYTHON = 'python3.11'
