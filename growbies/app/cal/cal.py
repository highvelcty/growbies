"""
cli:
    - start session
        - save identify state
        - set identify state
    - read_sensors(ref_masses)
    - read(ref_mass)
    - stop session
        - restore identify state
"""
import os
import pickle
import re

from growbies.utils.paths import InstallPaths
from growbies.device.common.identify import Identify
from growbies.service.cmd.nvm import identify
from growbies.utils.types import DeviceID

__all__ = ['DefaultCalSessionName', 'CalibrateSession']

class DefaultCalSessionName(str):
    DELIMITER = '-'
    TAG = 'calibration'
    SEARCH_TAG = f'{TAG}{DELIMITER}'
    FMT = f'{SEARCH_TAG}{{:d}}'
    _PATTERN = re.compile(rf"^{TAG}{DELIMITER}(\d+)$")

    def __new__(cls, value: int | str | None = None):
        # create the string value before returning
        if value is None:
            return super().__new__(cls, cls.FMT.format(0))

        if isinstance(value, int):
            return super().__new__(cls, cls.FMT.format(value))

        if isinstance(value, str):
            m = cls._PATTERN.match(value)
            if not m:
                raise ValueError(
                    f'Invalid default calibration session name "{value}", '
                    f'expected format: "{cls.SEARCH_TAG}<int>"'
                )
            return super().__new__(cls, value)

        raise TypeError(
            f"Expected int, str, or None; got {value!r} ({type(value).__name__})"
        )

    @property
    def idx(self) -> int:
        # parse the numeric suffix
        return int(self.split(self.DELIMITER)[-1])


class CalibrationData:
    def __init__(self, telemetry_interval):
        self._telemetry_interval = telemetry_interval

    @property
    def telemetry_interval(self):
        return self._telemetry_interval

class CalibrateSession:
    _PREFIX = 'calibrate_'
    _POSTFIX = '.pkl'
    _FILE_FMT = f'{_PREFIX}{{device_id}}{_POSTFIX}'

    def __init__(self, device_id: DeviceID):
        self._device_id = device_id
        self._path = (InstallPaths.RUN_GROWBIES.value / self._FILE_FMT.format(device_id=device_id))

    def save(self):
        if not self._path.exists():
            _ident = identify.get(self._device_id)
            calibration_data = CalibrationData(_ident.payload.telemetry_interval)
            with open(self._path, 'wb') as outf:
                # noinspection PyTypeChecker
                pickle.dump(calibration_data, outf)

    def restore(self):
        try:
            with open(self._path, 'rb') as inf:
                cal_data = pickle.load(inf)
                identify.update(
                    self._device_id,
                    {Identify.Field.TELEMETRY_INTERVAL: cal_data.telemetry_interval})
            os.remove(self._path)
        except FileNotFoundError:
            pass
