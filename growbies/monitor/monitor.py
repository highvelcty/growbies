import logging
import time

from growbies.arduino.arduino import Arduino
from growbies.sample.sample import COLUMN_STR
from growbies.session import Session
from growbies.utils.timestamp import get_utc_iso_ts_str, ContextElapsedTime
from growbies.utils.filelock import FileLock

POLLING_SEC = 0.5
OSERROR_RETRIES = 5
OSERROR_RETRY_DELAY_SECOND = 1
SAMPLING_RETRIES = 5
CHANNELS = 4
logger = logging.getLogger(__name__)

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
                outf.write(COLUMN_STR)
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
                    data = arduino_serial.read_units()

                    # total = sum(data.sensor[ii].mass for ii in range(4))
                    # file_str = (f'{ts}, {data.sensor[0].mass}, {data.sensor[1].mass}, '
                    #            f'{data.sensor[2].mass}, {data.sensor[3].mass}')
                    # out_str = (f'{ts}, {data.sensor[0].mass:.2f}, {data.sensor[1].mass:.2f}, '
                    #            f'{data.sensor[2].mass:.2f}, {data.sensor[3].mass:.2f}, {total:.2f}')
                    # out_str = (f'{ts}, {data.sensor[0].mass.data}, {data.sensor[1].mass.data}, '
                    #            f'{data.sensor[2].mass.data}, {data.sensor[3].mass.data}, '
                    #            f'{data.sensor[1].temperature.data}')
                    # out_str = (f'{ts}, {data.sensor[0].mass.data}, '
                    #            f'{data.sensor[0].temperature.data}')
                    out_str = (f'{ts}, {data.sensor[0].mass.data},'
                               f' {data.sensor[0].temperature.data}')
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
