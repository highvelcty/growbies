from typing import Optional
import logging
import time

from growbies.arduino.arduino import Arduino
from growbies.session import Session
from growbies.utils.timestamp import get_utc_iso_ts_str, ContextElapsedTime
from growbies.utils.filelock import FileLock

POLLING_SEC = 1
OSERROR_RETRIES = 5
OSERROR_RETRY_DELAY_SECOND = 1
SAMPLING_RETRIES = 5
CHANNELS = 4
logger = logging.getLogger(__name__)

def _continue_stream(sess: Session):
    with FileLock(), open(sess.path_to_data, 'a+') as outf:
        idx = outf.tell()
        while True:
            idx = max(0, idx - 1)
            outf.seek(idx)
            read_char = outf.read(1)
            if read_char == '\n':
                outf.seek(idx + 1)
                break
            if idx == 0:
                outf.write('timestamp,load_cell_scale,kitchen_scale\n')
                break
        outf.truncate()


def main(sess: Session):
    arduino_serial = Arduino()
    iteration = 0
    # Note: logging is intentionally avoided this retry loop. This is because the errors being
    # handled are likely due to temporary unavailability of the host file system. Logging also
    # accesses the file system and would further complicate the matter.

    arduino_serial.set_scale(1)
    arduino_serial.tare()

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
                    if sampling_retry:
                        logger.warning('Sampling retry.')

                    # Sample
                    ts = get_utc_iso_ts_str()
                    # sample = arduino_serial.read_average()
                    sample = arduino_serial.get_units()

                    if sample is None:
                        sampling_retry += 1
                    if sample is not None:
                        sampling_retry = 0
                        out_str = f'{ts},{sample},'
                        with FileLock(), open(sess.path_to_data, 'a+') as outf:
                            outf.write(f'{out_str}\n')
                        print(f'{str(elapsed_time)}: {out_str}')
                        iteration += 1

                    time.sleep(POLLING_SEC)
            except OSError:
                # print here instead of log because it is likely the host file system is not available.
                print(f'OSError encountered during monitor.')
                continue
            except KeyboardInterrupt:
                break
        else:
            print(f'Exhausted {OSERROR_RETRIES} OSError retries. See log for exception details.')
