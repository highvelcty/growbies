import ctypes
from typing import TextIO
import logging
import time

from growbies.arduino.arduino import ArduinoSerial
from growbies.session import Session
from growbies.utils.timestamp import get_utc_iso_ts_str

POLLING_SEC = 1
OSERROR_RETRIES = 5
OSERROR_RETRY_DELAY_SECOND = 1
SAMPLING_RETRIES = 5
logger = logging.getLogger(__name__)

class DataIn(ctypes.Structure):
    _fields_ = [
        ('data', ctypes.c_uint16 * ArduinoSerial.NUMBER_OF_CHANNELS)
    ]


def _continue_stream(outf: TextIO):
    idx = outf.tell()
    while True:
        idx = max(0, idx - 1)
        outf.seek(idx)
        read_char = outf.read(1)
        if read_char == '\n':
            break
        if idx == 0:
            outf.write('timestamp,channel0,channel1,channel2,channel3,channel4,channel5,channel6,'
                       'channel7\n')
            break
    outf.truncate()

def main(sess: Session):
    arduino_serial = ArduinoSerial()
    iteration = 0
    # Note: logging is intentionally avoided this retry loop. This is because the errors being
    # handled are likely due to temporary unavailability of the host file system. Logging also
    # accesses the file system and would further complicate the matter.
    sampling_retry = 0
    for retry in range(OSERROR_RETRIES):
        if retry:
            # print here instead of log because it is likely the host file system is not available.
            print(f'OSError retry {retry} / {OSERROR_RETRIES}')
            time.sleep(OSERROR_RETRY_DELAY_SECOND)
        try:
            with open(sess.path_to_data, 'a+') as outf:
                _continue_stream(outf)
                while True:
                    if sampling_retry > SAMPLING_RETRIES:
                        logger.error(f'Sampling persistently fails with {SAMPLING_RETRIES} '
                                     f'retries.')
                    if sampling_retry:
                        logger.warning('Sampling retry.')

                    # Sample
                    ts = get_utc_iso_ts_str()
                    samples = arduino_serial.sample()

                    if samples is None:
                        sampling_retry += 1
                    if samples is not None:
                        sampling_retry = 0
                        outf.write(f'{ts},' + ','.join((str(sample) for sample in samples.data))
                                   + '\n')
                        logger.info(f'{iteration}: {[sample for sample in samples.data]}')
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
