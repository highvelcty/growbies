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
from argparse import Namespace

from growbies.utils.types import SessionID
from growbies.device.common.identify import TNvmIdentify

CALIBRATION_TAG = 'calibration'

class Arguments:
    def __init__(self, args: Namespace):

    @property
    def session_id(self) -> SessionID:
        ...

    @property
    def ref_mass(self) -> float:
        ...

    @property
    def sensor_ref_mass(self) -> list[float]:
        ...

class CachedIdentify:
    def __init__(self, nvm_identify: TNvmIdentify):
        ...

    def restore(self):
        ...

class CalibrationSession:
    def __init__(self, session_id: SessionID):
        ...

    def stop(self):
        ...

    def __str__(self):
        ...


def main():
    parse_args()
    save_

if __name__ == '__main__':
    main()
