import time

from precision_farming.arduino.arduino import arduino_serial
from precision_farming.utils.paths import Paths
from precision_farming.utils.timestamp import get_utc_iso_ts_str

POLLING_SEC = 1

def main():
    iteration = 0
    with open(Paths.DATA_FILE.value, 'w') as outf:
        try:
            while True:
                sample = arduino_serial.sample()
                ts = get_utc_iso_ts_str()
                outf.write(f'{ts},{sample}\n')
                print(f'{iteration}: {sample}')
                iteration += 1
                time.sleep(POLLING_SEC)
        except KeyboardInterrupt:
            pass
