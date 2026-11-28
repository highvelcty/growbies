#!/usr/bin/python3

import subprocess
import shlex
import sys

def main():
    fuzzy_id = 'f8c'

    # Set True to simply plug the given values into the tables. Set False to add the given
    # values to the values in the table.
    overwrite_not_update = False

    # Insert `None` or omit to keep existing.
    new_sensor_coeffs = {
        0: (None, None, None, 2.291927, -.159622, .001041),
        1: (None, None, None, -4.643151, .103710, -.003116),
        2: (None, None, None, 1.205361, -.243947, .003015),
    }

    proc = run(f"growbies nvm cal {fuzzy_id}")
    existing_table = proc.stdout

    existing_coeffs = _parse_table(existing_table)

    updated_coeffs = {
        0: [],
        1: [],
        2: []
    }
    for sensor_idx, new_coeffs in new_sensor_coeffs.items():
        for coeff_idx, new_coeff in enumerate(new_coeffs):
            if new_coeff is None:
                updated_coeffs[sensor_idx].append(existing_coeffs[sensor_idx][coeff_idx])
            else:
                if overwrite_not_update:
                    updated_coeffs[sensor_idx].append(new_coeff)
                else:
                    updated_coeffs[sensor_idx].append(existing_coeffs[sensor_idx][coeff_idx] + new_coeff)

    for sensor_idx, coeffs in updated_coeffs.items():
        cmd = (
                f"growbies nvm cal {fuzzy_id} --coeffs {sensor_idx} "
                + " ".join(f'{c:.6f}' for c in coeffs)
        )
        run(cmd)
    proc = run(f'growbies nvm cal {fuzzy_id}')

def _parse_table(existing_table: str):
    sensor_coeffs = {}
    existing_table = existing_table.replace('|', '')
    for line in existing_table.splitlines():
        tokens = line.split()
        try:
            idx = int(tokens[0])
            sensor_coeffs[idx] = (float(tokens[1]), float(tokens[2]), float(tokens[3]),
                                  float(tokens[4]), float(tokens[5]), float(tokens[6]))
        except (ValueError, IndexError):
            pass
    return sensor_coeffs


def run(cmd: str) -> subprocess.CompletedProcess:
    print(f"\n$ {cmd}", flush=True)

    proc = subprocess.run(
        shlex.split(cmd),
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )

    if proc.stdout:
        print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")

    if proc.stderr:
        print(proc.stderr, end="" if proc.stderr.endswith("\n") else "\n")

    return proc

if __name__ == '__main__':
    main()
