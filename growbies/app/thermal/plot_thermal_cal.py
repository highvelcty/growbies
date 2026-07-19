#!/usr/bin/env python3

import argparse
from datetime import timezone

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


DEFAULT_FILE = "/tmp/thermal_cal.csv"


def load_data(filename):
    df = pd.read_csv(filename)

    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        utc=True,
    )

    # Convert boolean-like fields if they came through CSV as strings
    for field in [
        "active",
        "heater_on",
        "fan_on",
    ]:
        if field in df:
            df[field] = (
                df[field]
                .astype(str)
                .str.lower()
                .map(
                    {
                        "true": 1,
                        "false": 0,
                        "1": 1,
                        "0": 0,
                    }
                )
            )

    return df


def format_time_axis(ax):
    locator = mdates.AutoDateLocator()

    formatter = mdates.DateFormatter(
        "%Y-%m-%dT%H:%M:%S.%fZ",
        tz=timezone.utc,
    )

    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)

    ax.grid(True)

    plt.setp(
        ax.get_xticklabels(),
        rotation=45,
        ha="right",
    )


def plot_temperature(df):
    fig, ax = plt.subplots()

    ax.plot(
        df["timestamp"],
        df["temperature"],
        label="Temperature (°C)",
    )

    ax.plot(
        df["timestamp"],
        df["set_point"],
        label="Set Point (°C)",
    )

    ax.set_ylabel("Temperature (°C)")
    ax.set_title("Thermal Chamber Temperature")

    ax.legend()

    format_time_axis(ax)

    return fig


def plot_outputs(df):
    fig, ax = plt.subplots()

    ax.plot(
        df["timestamp"],
        df["duty_cycle"],
        label="Duty Cycle (%)",
    )

    ax.step(
        df["timestamp"],
        df["heater_on"] * 100,
        where="post",
        label="Heater On",
    )

    ax.step(
        df["timestamp"],
        df["fan_on"] * 100,
        where="post",
        label="Fan On",
    )

    ax.set_ylabel("Percent / State")
    ax.set_ylim(-5, 105)

    ax.set_title("Thermal Outputs")

    ax.legend()

    format_time_axis(ax)

    return fig


def plot_controller(df):
    fig, ax = plt.subplots()

    ax.plot(
        df["timestamp"],
        df["controller_proportional_term"],
        label="P term",
    )

    ax.plot(
        df["timestamp"],
        df["controller_integral_term"],
        label="I term",
    )

    ax.set_ylabel("Controller Contribution")

    ax.set_title("PI Controller Terms")

    ax.legend()

    format_time_axis(ax)

    return fig


def plot_errors(df):
    fig, ax = plt.subplots()

    error_mask = df["error"].notna() & (df["error"] != "0: NONE")

    errors = df[error_mask]

    if len(errors):
        ax.scatter(
            errors["timestamp"],
            range(len(errors)),
        )

        for _, row in errors.iterrows():
            ax.annotate(
                row["error"],
                (row["timestamp"], 0),
                rotation=45,
                fontsize=8,
            )

    ax.set_title("Errors")

    format_time_axis(ax)

    return fig


def print_summary(df):
    start = df["timestamp"].iloc[0]
    end = df["timestamp"].iloc[-1]

    elapsed = end - start

    print()
    print("Thermal Log Summary")
    print("-------------------")
    print(f"Samples:       {len(df)}")
    print(f"Start:         {start}")
    print(f"End:           {end}")
    print(f"Duration:      {elapsed}")

    print()

    print(
        "Temperature:"
    )
    print(
        f"  Min: {df.temperature.min():.2f} °C"
    )
    print(
        f"  Max: {df.temperature.max():.2f} °C"
    )
    print(
        f"  Avg: {df.temperature.mean():.2f} °C"
    )

    print()

    print(
        "Duty cycle:"
    )
    print(
        f"  Avg: {df.duty_cycle.mean():.2f}%"
    )

    print()


def main():

    parser = argparse.ArgumentParser(
        description="Plot thermal chamber calibration data"
    )

    parser.add_argument(
        "file",
        nargs="?",
        default=DEFAULT_FILE,
        help="CSV file",
    )

    args = parser.parse_args()

    df = load_data(args.file)

    print_summary(df)

    plot_temperature(df)
    plot_outputs(df)
    plot_controller(df)
    plot_errors(df)

    plt.show()


if __name__ == "__main__":
    main()