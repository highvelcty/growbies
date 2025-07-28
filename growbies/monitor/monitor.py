import logging
import time

from growbies.arduino.arduino import Arduino
from growbies.arduino.structs.command import MASS_SENSOR_COUNT
from growbies.arduino.structs.command import TEMPERATURE_SENSOR_COUNT
from growbies.arduino.structs.command import CmdReadUnits
from growbies.session import Session
from growbies.utils.timestamp import get_utc_iso_ts_str, ContextElapsedTime
from growbies.utils.filelock import FileLock

POLLING_SEC = 0.5
OSERROR_RETRIES = 5
OSERROR_RETRY_DELAY_SECOND = 1
SAMPLING_RETRIES = 5
CHANNELS = 4
logger = logging.getLogger(__name__)
COLUMN_STR = ''.join(
             ['timestamp, '] +
             [f'mass_sensor_{ii}, ' for ii in range(MASS_SENSOR_COUNT)] +
             [f'mass, '] +
             [f'temperature_sensor_{ii}, ' for ii in range(TEMPERATURE_SENSOR_COUNT)] +
             [f'temperature'])

def _continue_stream(sess: Session):
    with FileLock(sess.path_to_data, 'a+') as outf:
        idx = outf.tell()
        while True:
            idx = max(0, idx - 1)
            outf.seek(idx)
            read_char = outf.read(1)
            if read_char == '\n':
                outf.seek(idx + 1)
                break
            if idx == 0:
                outf.write(COLUMN_STR + '\n')
                # outf.write('timestamp,load_cell_scale,kitchen_scale\n')
                break
        outf.truncate()

def main(sess: Session):
    arduino_serial = Arduino()
    iteration = 0
    # Note: logging is intentionally avoided this retry loop. This is because the errors being
    # handled are likely due to temporary unavailability of the host file system. Logging also
    # accesses the file system and would further complicate the matter.

    with ContextElapsedTime() as elapsed_time:
        sampling_retry = 0
        for retry in range(OSERROR_RETRIES):
            if retry:
                # print here instead of log because it is likely the host file system is not available.
                print(f'OSError retry {retry} / {OSERROR_RETRIES}')
                time.sleep(OSERROR_RETRY_DELAY_SECOND)
            try:
                _continue_stream(sess)
                while True:
                    if sampling_retry > SAMPLING_RETRIES:
                        logger.error(f'Sampling persistently fails with {SAMPLING_RETRIES} '
                                     f'retries.')
                        break
                    if sampling_retry:
                        logger.warning('Sampling retry.')


                    ts = get_utc_iso_ts_str()
                    resp = arduino_serial.read_dac(CmdReadUnits.DEFAULT_TIMES)
                    out_str = ''.join(
                            [f'{ts}, '] +
                            [f'{resp.mass_sensor[ii]}, ' for ii in range(MASS_SENSOR_COUNT)] +
                            [f'{resp.mass}, '] +
                            [f'{resp.temperature_sensor[ii]}, ' for ii in range(
                                TEMPERATURE_SENSOR_COUNT)] +
                            [f'{resp.temperature}']
                    )
                    file_str = out_str

                    with FileLock(sess.path_to_data, 'a+') as outf:
                        outf.write(f'{file_str}\n')
                    print(out_str)

                    time.sleep(POLLING_SEC)
            except OSError:
                # print here instead of log because it is likely the host file system is not available.
                print(f'OSError encountered during monitor.')
                continue
            except KeyboardInterrupt:
                break
        else:
            print(f'Exhausted {OSERROR_RETRIES} OSError retries. See log for exception details.')
