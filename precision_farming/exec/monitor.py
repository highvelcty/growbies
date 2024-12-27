import time

from precision_farming.arduino.arduino import ArduinoSerial
from precision_farming.session import Session
from precision_farming.utils.timestamp import get_utc_iso_ts_str

POLLING_SEC = 1

def main(sess: Session):
    arduino_serial = ArduinoSerial()
    iteration = 0
    with open(sess.path_to_data, 'w') as outf:
        outf.write('timestamp,channel0,channel1,channel2,channel3\n')
        try:
            while True:
                ts = get_utc_iso_ts_str()
                samples = arduino_serial.sample()
                outf.write(f'{ts},')
                for idx, sample in enumerate(samples):
                    if idx != len(samples) - 1:
                        outf.write(f'{sample},')
                    else:
                        outf.write(f'{sample}\n')
                print(f'{iteration}: {samples}')
                iteration += 1
                time.sleep(POLLING_SEC)
        except KeyboardInterrupt:
            pass
