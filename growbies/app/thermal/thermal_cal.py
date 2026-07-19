#!/usr/bin/env python3

import csv
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from prettytable import PrettyTable


OUTPUT_FILE = Path("/tmp/thermal_cal.csv")
COMMAND = ["growbies", "thermal", "thermal-chamber-1"]
PERIOD_SECONDS = 5


FIELDS = [
    "timestamp",
    "active",
    "mode",
    "duty_cycle",
    "set_point",
    "heater_on",
    "fan_on",
    "temperature",
    "controller_proportional_term",
    "controller_integral_term",
    "error",
]


class RunStatistics:
    def __init__(self):
        self.start_time = time.monotonic()
        self.samples = 0
        self.errors = 0

    def elapsed(self):
        seconds = int(time.monotonic() - self.start_time)

        days, seconds = divmod(seconds, 86400)
        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)

        return (
            f"{days}d "
            f"{hours:02d}h "
            f"{minutes:02d}m "
            f"{seconds:02d}s"
        )

    def table(self):
        table = PrettyTable(title="Thermal Run Statistics")
        table.field_names = ["Field", "Value"]
        table.align["Field"] = "l"

        table.add_row(["Elapsed Time", self.elapsed()])
        table.add_row(["Samples", self.samples])
        table.add_row(["Errors", self.errors])

        return table


def utc_timestamp():
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def parse_value(value):
    value = value.strip()

    if value in ("True", "False"):
        return value == "True"

    return value


def parse_table(lines):
    result = {}

    for line in lines:
        if "|" not in line:
            continue

        parts = [
            part.strip()
            for part in line.split("|")
        ]

        if len(parts) != 4:
            continue

        field = parts[1]
        value = parts[2]

        if field in ("Field", ""):
            continue

        result[field] = parse_value(value)

    return result


def parse_percent(value):
    if value is None:
        return None

    try:
        return float(value.replace("%", "").strip())
    except ValueError:
        return None


def parse_temperature_c(value):
    if value is None:
        return None

    try:
        # Expected format:
        # "1.22 °C (34.20 °F)"
        return float(value.split("°C")[0].strip())
    except (ValueError, IndexError):
        return None


def parse_float(value):
    if value is None:
        return None

    try:
        return float(value.strip())
    except ValueError:
        return None

def parse_output(output):
    sections = output.split("\n\n")

    control = {}
    sense = {}

    for section in sections:
        if "Thermal Device Control" in section:
            control = parse_table(section.splitlines())

        elif "Thermal Device Sense" in section:
            sense = parse_table(section.splitlines())

    return {
        "timestamp": utc_timestamp(),

        "active": control.get("active"),
        "mode": control.get("mode"),
        "duty_cycle": parse_percent(control.get("duty_cycle")),
        "set_point": parse_temperature_c(control.get("set_point")),

        "heater_on": sense.get("heater_on"),
        "fan_on": sense.get("fan_on"),
        "temperature": parse_temperature_c(sense.get("temperature")),

        "controller_proportional_term": parse_float(
            sense.get("controller_proportional_term")
        ),
        "controller_integral_term": parse_float(
            sense.get("controller_integral_term")
        ),

        "error": sense.get("error"),
    }

def null_row(error):
    return {
        field:
            utc_timestamp()
            if field == "timestamp"
            else error
            if field == "error"
            else None
        for field in FIELDS
    }


def run_command(stats):
    try:
        result = subprocess.run(
            COMMAND,
            capture_output=True,
            text=True,
            check=True,
        )

        stats.samples += 1

        return parse_output(result.stdout)

    except subprocess.CalledProcessError as exc:
        stats.errors += 1
        return null_row(
            f"return_code={exc.returncode}"
        )

    except OSError as exc:
        stats.errors += 1
        return null_row(
            f"{exc.errno}: {exc.strerror}"
        )


def append_csv(row):
    exists = OUTPUT_FILE.exists()

    with OUTPUT_FILE.open("a", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=FIELDS,
        )

        if not exists:
            writer.writeheader()

        writer.writerow(row)


def print_state(row, stats):
    control = PrettyTable(title="Thermal Device Control")
    control.field_names = ["Field", "Value"]
    control.align["Field"] = "l"

    for field in [
        "active",
        "mode",
        "duty_cycle",
        "set_point",
    ]:
        control.add_row([
            field,
            row[field],
        ])

    sense = PrettyTable(title="Thermal Device Sense")
    sense.field_names = ["Field", "Value"]
    sense.align["Field"] = "l"

    for field in [
        "heater_on",
        "fan_on",
        "temperature",
        "controller_proportional_term",
        "controller_integral_term",
        "error",
    ]:
        sense.add_row([
            field,
            row[field],
        ])

    print("\033[2J\033[H", end="")  # clear terminal

    print(control)
    print()
    print(sense)
    print()
    print(stats.table())


def main():
    stats = RunStatistics()

    while True:
        row = run_command(stats)

        append_csv(row)

        print_state(row, stats)

        time.sleep(PERIOD_SECONDS)


if __name__ == "__main__":
    main()


