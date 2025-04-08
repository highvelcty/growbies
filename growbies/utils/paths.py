from enum import Enum
from pathlib import Path

from growbies import constants

class RepoPaths(Enum):
    # .
    REPO_ROOT = Path('.')
    DOT_COVERAGE = REPO_ROOT / '.coverage'

    # ./.idea
    DOT_IDEA = REPO_ROOT / '.idea'

    # ./build
    BUILD = REPO_ROOT / 'build'
    BUILD_PATHS_ENV = BUILD / 'paths.env'

    # ./dist
    DIST = REPO_ROOT / 'dist'

    # ./db
    DB = REPO_ROOT / 'db'
    DB_INIT_SH = DB / 'init.sh'

    # ./growbies
    GROWBIES = REPO_ROOT / 'growbies'
    GROWBIES_EXEC = GROWBIES / 'exec'
    GROWBIES_HUMAN_INPUT = GROWBIES / 'human_input'
    GROWBIES_MONITOR = GROWBIES / 'monitor'
    GROWBIES_PLOT = GROWBIES / 'plot'
    GROWBIES_SAMPLE = GROWBIES / 'sample'
    GROWBIES_SERVICE = GROWBIES / 'service'

    # ./output
    OUTPUT = REPO_ROOT / 'output'
    DEFAULT_OUTPUT_DIR = OUTPUT / 'default'
    DEFAULT_LOG = OUTPUT / 'log.log'
    DEFAULT_DATA = DEFAULT_OUTPUT_DIR / 'data.csv'
    FILELOCK = OUTPUT / 'file.lock'

    # ./pkg
    PKG = REPO_ROOT / 'pkg'
    PKG_BASH_SRC = PKG / 'bash_src'
    PKG_BASH_SRC_GROWBIES = PKG_BASH_SRC / 'growbies'
    PKG_DEB = PKG / 'deb'
    PKG_DEB_DEBIAN = PKG_DEB / 'debian'
    PKG_DEB_DEBIAN_SRC = PKG_DEB_DEBIAN / 'src'
    PKG_DEB_DIST = PKG_DEB / 'dist'
    PKG_DEB_REPO = PKG_DEB / 'repo'


class InstallPaths(Enum):
    # /usr/lib
    USR_LIB = Path('/usr/lib')
    USR_LIB_GROWBIES = USR_LIB / constants.APPNAME.lower()
    # /var/opt/db
    USR_LIB_GROWBIES_DB = USR_LIB_GROWBIES / 'db'
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
    DEBIAN_ROOT = Path(RepoPaths.PKG_DEB_DEBIAN.value.name)
    DEBIAN_BUILD_SH = DEBIAN_ROOT / 'build.sh'
    DEBIAN_INSTALL_SH = DEBIAN_ROOT / 'install.sh'
    DEBIAN_SRC = DEBIAN_ROOT / 'src'

    # command
    DEBIAN_BASE_PYTHON = 'python3.11'
