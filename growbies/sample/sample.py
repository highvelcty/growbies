from growbies.arduino import Arduino
from growbies.session import Session
from growbies.utils.timestamp import get_utc_iso_ts_str

COLUMN_STR = ('Timestamp,channel_0 mass,channel_1 mass,channel_2 mass,channel_3 mass,'
              'reference mass (grams)\n')

def main(sess: Session):
    ser = Arduino()

    # Get reference input
    while True:
        while True:
            ref = input('Reference mass:')
            try:
                ref = int(ref)
                break
            except ValueError:
                print(f'Cannot convert "{ref}" to integer. Please try again.', ref)
                continue

        # Sample scale under test
        samples = list()
        for channel in range(4):
            ser.set_channel(channel)
            samples.append(ser.read_average())
        ts = get_utc_iso_ts_str()

        # Output data to file
        if not sess.path_to_data.exists():
            with open(sess.path_to_data, 'w') as outf:
                outf.write(COLUMN_STR)
        with open(sess.path_to_data, 'a+') as outf:
            outf.write(f'{ts},{samples[0]},{samples[1]},{samples[2]},{samples[3]},{ref}\n')
            
