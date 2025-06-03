from enum import Enum
from pathlib import Path

from growbies import constants

_REPO_ROOT = Path(__file__).parent.parent.parent.resolve()

class RepoPaths(Enum):
    # .
    REPO_ROOT = Path('.')
    DOT_COVERAGE = REPO_ROOT / '.coverage'

    # ./.idea
    DOT_IDEA = REPO_ROOT / '.idea'

    # ./archive
    ARCHIVE = REPO_ROOT / 'archive'

    # ./build
    BUILD = REPO_ROOT / 'build'
    BUILD_PATHS_ENV = BUILD / 'paths.env'

    # ./build_lib
    BUILD_LIB = REPO_ROOT / 'build_lib'

    # ./dist
    DIST = REPO_ROOT / 'dist'

    # ./docs
    DOCS = REPO_ROOT / 'docs'

    # ./endpoint
    ENDPOINT = REPO_ROOT / 'endpoint'
    ENDPOINT_ARDUINO = ENDPOINT / 'arduino'

    # ./growbies
    GROWBIES = REPO_ROOT / 'growbies'
    GROWBIES_DB = GROWBIES / 'db'
    GROWBIES_DB_SQL = GROWBIES_DB / 'sql'
    GROWBIES_DB_SQL_INIT_TABLES = GROWBIES_DB_SQL / 'init_tables.sql'
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

    # ./tests
    TESTS = REPO_ROOT / 'tests'

    @classmethod
    def abs(cls, path: 'RepoPaths'):
        return _REPO_ROOT / path.value

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
    DEBIAN_SRC_GROWBIES = DEBIAN_SRC / RepoPaths.GROWBIES.value
    DEBIAN_SRC_PKG_BASH_SRC = DEBIAN_SRC / RepoPaths.PKG_BASH_SRC.value

    # command
    DEBIAN_BASE_PYTHON = 'python3.11'
