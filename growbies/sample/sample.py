from growbies.arduino import Arduino
from growbies.session import Session
from growbies.utils.timestamp import get_utc_iso_ts_str

COLUMN_STR = 'Timestamp,mass_sensor_0,mass_sensor_1,mass_sensor_2,temperature,reference mass\n'

def main(sess: Session):
    arduino = Arduino()

    # Get reference input
    while True:
        while True:
            ref_mass = input('Reference mass:')
            try:
                ref_mass = float(ref_mass)
                break
            except ValueError:
                print(f'Cannot convert "{ref_mass}" to float. Please try again.', ref_mass)
                continue

        # Sample scale under test
        samples = list()
        ts = get_utc_iso_ts_str()
        data = arduino.read_units(7)

        # Initialize output file if necessary
        if not sess.path_to_data.exists():
            with open(sess.path_to_data, 'w') as outf:
                outf.write(COLUMN_STR)

        # Write out data to file
        out_str = (f'{ts}, '
                   f'{data.sensor[0].mass.data}, '
                   f'{data.sensor[1].mass.data}, '
                   f'{data.sensor[2].mass.data}, '
                   f'{data.sensor[0].temperature.data}, '
                   f'{ref_mass}')
        with open(sess.path_to_data, 'a+') as outf:
            outf.write(f'{out_str}\n')
        print(out_str)

