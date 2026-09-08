#!/usr/bin/env python3

import subprocess
import sys
import time


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

THERMAL_DEVICE = "therm"

# Devices to calibrate.
DEVICES = [
    "205",
    "696",
    "871",
    "8e9",
    "bc7b",
]

# Temperature set points, in degrees Celsius.
SET_POINTS = [
    25.0,
    30.0,
    35.0,
    40.0,
    45.0,
    50.0,
]

# The measured chamber temperature must be within this many degrees of the
# set point before the dwell begins.
TEMPERATURE_TOLERANCE_C = 0.5

# Time that the chamber must remain at temperature before sampling.
DWELL_SECONDS = 3 * 60

# How often to check the chamber temperature while waiting.
THERMAL_POLL_SECONDS = 10


# ---------------------------------------------------------------------------
# Status output
# ---------------------------------------------------------------------------

def print_status(message):
    """Update the current terminal status line without cluttering the screen."""

    width = max(print_status.last_length, len(message))

    print(
        f"\r{message:<{width}}",
        end="",
        flush=True,
    )

    print_status.last_length = len(message)


print_status.last_length = 0


def clear_status():
    """Clear the current terminal status line."""

    print_status("")


# ---------------------------------------------------------------------------
# Thermal chamber
# ---------------------------------------------------------------------------
def get_chamber_temperature():
    """Return the chamber temperature in degrees Celsius."""

    result = subprocess.run(
        ["growbies", "thermal", THERMAL_DEVICE],
        capture_output=True,
        text=True,
        check=True,
    )

    for line in result.stdout.splitlines():
        if "temperature" not in line:
            continue

        # Expected:
        #
        # | temperature             | 21.89 °C (71.41 °F) |
        #
        # Extract the value immediately before °C.
        try:
            value = line.split("|")[2].strip()
            return float(value.split("°C")[0].strip())
        except (IndexError, ValueError):
            pass

    raise RuntimeError("Could not find chamber temperature in thermal output")


def set_chamber_temperature(set_point):
    """Set and activate the thermal chamber."""

    result = subprocess.run(
        [
            "growbies",
            "thermal",
            THERMAL_DEVICE,
            "--activate",
            "--mode",
            "0",
            "--set-point",
            str(set_point),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )

    if result.returncode != 0:
        if result.stderr:
            sys.stderr.write(result.stderr)

        raise RuntimeError(
            f"Failed to set thermal chamber to {set_point:.2f} °C"
        )


# ---------------------------------------------------------------------------
# Calibration run
# ---------------------------------------------------------------------------
def wait_for_temperature(set_point):
    """Wait until the chamber reaches the requested temperature."""

    timeout = 60 * 60
    start = time.monotonic()

    print(f"Heating to {set_point:.1f} °C...", flush=True)

    while True:
        if time.monotonic() - start >= timeout:
            clear_status()
            print(
                f"ERROR: Timed out after 1 hour waiting for "
                f"{set_point:.1f} °C.",
                file=sys.stderr,
            )
            return False

        try:
            temperature = get_chamber_temperature()
        except Exception as exc:
            clear_status()
            print(f"ERROR: {exc}", file=sys.stderr)
            return False

        if abs(temperature - set_point) <= TEMPERATURE_TOLERANCE_C:
            clear_status()
            print(
                f"At temperature: {temperature:.2f} °C "
                f"(target {set_point:.2f} °C)"
            )
            return True

        print_status(
            f"  {temperature:.2f} °C "
            f"(target {set_point:.2f} °C)"
        )

        time.sleep(THERMAL_POLL_SECONDS)


def dwell(set_point):
    """Dwell at temperature for the configured duration."""

    clear_status()
    print(
        f"Beginning {DWELL_SECONDS // 60}-minute dwell "
        f"at {set_point:.1f} °C."
    )

    start = time.monotonic()
    next_progress = start

    while True:
        now = time.monotonic()
        elapsed = now - start

        if elapsed >= DWELL_SECONDS:
            break

        if now >= next_progress:
            remaining = DWELL_SECONDS - elapsed
            minutes_remaining = int((remaining + 59) // 60)

            print_status(
                f"  {minutes_remaining} minutes remaining"
            )

            next_progress += 60

        time.sleep(1)

    clear_status()
    print("Dwell complete.")


def sample():
    """Sample all DUTs in parallel."""

    processes = []

    for device_id in DEVICES:
        print_status(f"Sampling DUT {device_id}...")

        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "growbies.app.cal",
                "sample",
                "temp",
                device_id,
            ],
            stdout=subprocess.DEVNULL,
        )

        processes.append((device_id, process, time.monotonic()))

    for device_id, process, start in processes:
        return_code = process.wait()
        elapsed = time.monotonic() - start

        if return_code != 0:
            clear_status()
            print(
                f"ERROR: temperature sample failed for DUT {device_id} "
                f"(return code {return_code}, {elapsed:.1f} seconds)",
                file=sys.stderr,
            )

    clear_status()

    for device_id, process, start in processes:
        elapsed = time.monotonic() - start
        print_status(
            f"DUT {device_id} sampled in {elapsed:.1f} seconds"
        )
        time.sleep(0.5)

    clear_status()

def main():
    if not DEVICES:
        print("ERROR: DEVICES is empty.", file=sys.stderr)
        return 1

    if not SET_POINTS:
        print("ERROR: SET_POINTS is empty.", file=sys.stderr)
        return 1

    print("Growbies thermal calibration")
    print()

    try:
        for set_point in SET_POINTS:
            print(f"=== {set_point:.1f} °C ===")

            set_chamber_temperature(set_point)

            if not wait_for_temperature(set_point):
                return 1

            dwell(set_point)
            sample()

            print()

    except KeyboardInterrupt:
        clear_status()
        print("Calibration interrupted.", file=sys.stderr)
        return 1

    except Exception as exc:
        clear_status()
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print("Thermal calibration complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())