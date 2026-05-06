import logging
import sys
import time

from argparse import Namespace
import shlex, subprocess

from .cli import STDIN_LEVEL, STDOUT_LEVEL, STDERR_LEVEL
from growbies.cli.common import Param
from growbies.device.common import identify
from growbies.db.engine import get_db_engine

logger = logging.getLogger(__name__)

def run_cmd(cmd, check=False) -> tuple[int, str, str]:
    for line in cmd.splitlines():
        logger.log(STDIN_LEVEL, line)
    try:
        proc = subprocess.run(shlex.split(cmd), stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, check=check, encoding='utf-8')
    except (subprocess.CalledProcessError, FileNotFoundError) as err:
        logger.exception(err)
        return 1, '', ''
    else:
        if proc.stdout:
            for line in proc.stdout.splitlines():
                logger.log(STDOUT_LEVEL, line)
        if proc.stderr:
            for line in proc.stderr.splitlines():
                logger.log(STDERR_LEVEL, line)
        return proc.returncode, proc.stdout, proc.stderr

class DeviceSession:
    def __init__(self, fuzzy_id):
        self._fuzzy_id = fuzzy_id
        self._returncode = 0

    @property
    def returncode(self) -> int:
        return self._returncode

    def __enter__(self):
        self._returncode, _, _ = \
            run_cmd(f'growbies device activate {self._fuzzy_id}')
        if self._returncode:
            raise RuntimeError('Device activation failed')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self._returncode:
            self._returncode, _, _ = run_cmd(f'growbies device deactivate {self._fuzzy_id}')


class SetIdentification:
    def __init__(self, fuzzy_id):
        self._fuzzy_id = fuzzy_id
        self._db_engine = get_db_engine()
        self._dev = self._db_engine.device.get(self._fuzzy_id)
        self._returncode = 0
    _defaults = {
        identify.Identify.Field.MODEL_NUMBER.public_name: 'circle_10',
        identify.Identify.Field.PCBA.public_name: identify.PcbaType.ESP32C3,
        identify.Identify.Field.WIRELESS.public_name: identify.WirelessType.BLE,
        identify.Identify.Field.BATTERY.public_name: identify.BatteryType.LIPO_502030_250MAH,
        identify.Identify.Field.DISPLAY.public_name: identify.DisplayType.DORHEA,
        identify.Identify.Field.LED.public_name: identify.LedType.NONE,
        identify.Identify.Field.FRAME.public_name: identify.FrameType.CIRCLE_10,
        identify.Identify.Field.FOOT.public_name: identify.FootType.FLATTENED_SPHERE_40_x_25,
        'no-flip': '',
        identify.Identify.Field.MASS_UNITS.public_name: identify.MassUnitsType.GRAMS,
        identify.Identify.Field.TEMPERATURE_UNITS.public_name:
            identify.TemperatureUnitsType.FAHRENHEIT,
        identify.Identify.Field.CONTRAST.public_name: 128,
        identify.Identify.Field.TELEMETRY_INTERVAL.public_name: 0,
        identify.Identify.Field.SLEEP_TIMEOUT.public_name: 60.0,
        identify.Identify.Field.AUTO_WAKE_INTERVAL.public_name: 0.5
    }

    @property
    def returncode(self) -> int:
        return self._returncode

    def serial_number(self):
        rc, _, _ = run_cmd(f'growbies nvm id {self._fuzzy_id} --serial_number {self._dev.serial}')
        self._returncode |= rc

    def manufacture_date(self):
        rc, _, _ = run_cmd(f'growbies nvm id {self._fuzzy_id} --manufacture_date {time.time()}')
        self._returncode |= rc

    def set_defaults(self):
        for key, value in self._defaults.items():
            rc, _, _ = run_cmd(f'growbies nvm id {self._fuzzy_id} --{key} {value}')
            self._returncode |= rc

    def set_all(self):
        self.serial_number()
        self.manufacture_date()
        self.set_defaults()

def execute(args: Namespace):
    returncode = 0
    fuzzy_id = getattr(args, Param.FUZZY_ID)
    with DeviceSession(fuzzy_id) as dev_sess:
        id_setter = SetIdentification(fuzzy_id)
        id_setter.set_all()
        returncode |= id_setter.returncode

    returncode |= dev_sess.returncode

    if returncode == 0:
        logger.info('*** PASS ***')
    else:
        logger.error('*** FAIL ***')

    sys.exit(dev_sess.returncode)
