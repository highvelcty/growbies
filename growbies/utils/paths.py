from enum import Enum
from pathlib import Path

from growbies import constants

_REPO_ROOT = Path(__file__).parent.parent.parent.resolve()

# Putting paths into enums is a bit gnarly for static analysis
# noinspection PyUnresolvedReferences
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

    # ./growbies
    GROWBIES = REPO_ROOT / 'growbies'

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

    # ./tests
    TESTS = REPO_ROOT / 'tests'

    @classmethod
    def abs(cls, path: 'RepoPaths'):
        return _REPO_ROOT / path.value

# noinspection PyUnresolvedReferences
class InstallPaths(Enum):
    APPNAME = constants.APPNAME.lower()

    # /usr/bin
    USR_BIN = Path(f'/usr/bin')

    # /usr/lib
    USR_LIB =  Path(f'/usr/lib')
    USR_LIB_GROWBIES = USR_LIB / APPNAME
    USR_LIB_GROWBIES_VENV = USR_LIB_GROWBIES / 'venv'
    USR_LIB_GROWBIES_VENV_ACTIVATE = USR_LIB_GROWBIES_VENV / 'bin/activate'

    # /var/lib
    VAR_LIB = Path('/var/lib')
    VAR_LIB_GROWBIES = VAR_LIB / APPNAME

    # /var/lib/lock
    VAR_LIB_GROWBIES_LOCK = VAR_LIB_GROWBIES / 'lock'
    VAR_LIB_GROWBIES_LOCK_SERVICE = VAR_LIB_GROWBIES_LOCK / 'service.lock'

    # /var/log
    VAR_LOG = Path('/var/log')
    VAR_LOG_GROWBIES = VAR_LOG / APPNAME
    VAR_LOG_GROWBIES_LOG = VAR_LOG_GROWBIES / 'growbies.log'

    # /run/growbies
    # Note: created and available when "RuntimeDirectory=" is used in systemd service files
    RUN = Path('/run')
    RUN_GROWBIES = RUN / 'growbies'
    RUN_GROWBIES_CMD_Q = RUN_GROWBIES / 'cmd_queue.pkl'

    # /etc
    ETC = Path(f'/etc')
    ETC_GROWBIES = ETC / APPNAME
    ETC_GROWBIES_YAML = ETC_GROWBIES / 'growbies.yaml'

    SYS_BUS_USB_DEVICES = Path('/sys/bus/usb/devices')
    DEV = Path('/dev')
    DEV_TTY_STR = DEV / 'tty*'


# noinspection PyUnresolvedReferences,PyTypeChecker
class DebianPaths(Enum):
    # .
    DEBIAN_ROOT = Path(RepoPaths.PKG_DEB_DEBIAN.value.name)
    DEBIAN_BUILD_SH = DEBIAN_ROOT / 'build.sh'
    DEBIAN_INSTALL_SH = DEBIAN_ROOT / 'install.sh'
    DEBIAN_SRC = DEBIAN_ROOT / 'src'
    DEBIAN_SRC_GROWBIES = DEBIAN_SRC / RepoPaths.GROWBIES.value
    DEBIAN_SRC_PKG_BASH_SRC = DEBIAN_SRC / RepoPaths.PKG_BASH_SRC.value
    DEBIAN_SRC_BUILD_LIB = DEBIAN_SRC / 'build_lib'
    DEBIAN_SRC_BUILD_LIB_SET_VERSION_PY = DEBIAN_SRC_BUILD_LIB / 'set_version.py'

    # command
    DEBIAN_BASE_PYTHON = 'python3.11'

# noinspection PyUnresolvedReferences
class FirmwarePaths(Enum):
    FIRMWARE = Path(RepoPaths.REPO_ROOT.value) / 'firmware'
    FIRMWARE_PIO = FIRMWARE / '.pio'
    FIRMWARE_PIO_BUILD = FIRMWARE_PIO / 'build'
