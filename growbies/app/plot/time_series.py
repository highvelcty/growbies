from datetime import datetime, timezone
from collections import defaultdict

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter, AutoDateLocator, num2date
from sqlalchemy.engine.row import Row

from growbies.db.engine import get_db_engine
from growbies.common.utils.timestamp import get_elapsed_str


def plot_time_series(fuzzy_id: str, start_time: datetime, end_time: datetime):
    db_engine = get_db_engine()
    device = db_engine.device.get(fuzzy_id)
    device_id = device.id


    datapoints, mass_sensor_datapoints, temp_sensor_datapoints = \
        db_engine.datapoint.get_device_datapoints(
            device_id,
            start_time,
            end_time,
        )

    _plot_time_series(
        datapoints,
        mass_sensor_datapoints,
        temp_sensor_datapoints,
        device.name,
        device.serial
    )


def _plot_time_series(
        datapoints: list[Row],
        mass_sensor_datapoints: list[Row],
        temp_sensor_datapoints: list[Row],
        device_name: str,
        device_serial: str,
):

    timestamps = np.fromiter(
        (dp.timestamp for dp in datapoints),
        dtype="datetime64[ms]",
        count=len(datapoints),
    )

    mass = np.fromiter(
        (dp.mass for dp in datapoints),
        dtype=float,
        count=len(datapoints),
    )

    temperature = np.fromiter(
        (dp.temperature for dp in datapoints),
        dtype=float,
        count=len(datapoints),
    )

    fig, (
        (ax_mass, ax_sensor_mass),
        (ax_temp, ax_sensor_temp),
    ) = plt.subplots(
        2,
        2,
        figsize=(16, 10),
        sharex=True,
    )

    fig.suptitle(f'Name: {device_name}\n'
                 f'Serial: {device_serial}\n')

    axes = [
        ax_mass,
        ax_sensor_mass,
        ax_temp,
        ax_sensor_temp,
    ]

    # -------------------------
    # Aggregate plots
    # -------------------------

    ax_mass.plot(
        timestamps,
        mass,
        color="blue",
    )

    ax_mass.set_ylabel("Mass (g)")
    ax_mass.set_title("Aggregate Mass")


    ax_temp.plot(
        timestamps,
        temperature,
        color="red",
    )

    ax_temp.set_ylabel("Temperature (°C)")
    ax_temp.set_title("Aggregate Temperature")


    # -------------------------
    # Sensor plots
    # -------------------------

    sensor_colors = [
        "cyan",
        "magenta",
        "gray",
    ]

    sensor_mass_arrays = {}
    sensor_temp_arrays = {}

    sensor_mass_lists = defaultdict(lambda: ([], []))
    sensor_temp_lists = defaultdict(lambda: ([], []))

    for row in mass_sensor_datapoints:
        sensor_mass_lists[row.idx][0].append(row.timestamp)
        sensor_mass_lists[row.idx][1].append(row.mass)

    for row in temp_sensor_datapoints:
        sensor_temp_lists[row.idx][0].append(row.timestamp)
        sensor_temp_lists[row.idx][1].append(row.temperature)


    for idx, (times, values) in sensor_mass_lists.items():

        times = np.asarray(
            times,
            dtype="datetime64[ms]",
        )

        values = np.asarray(
            values,
            dtype=float,
        )

        sensor_mass_arrays[idx] = (
            times,
            values,
        )

        ax_sensor_mass.plot(
            times,
            values,
            color=sensor_colors[idx % len(sensor_colors)],
            label=f"Sensor {idx}",
        )


    for idx, (times, values) in sensor_temp_lists.items():

        times = np.asarray(
            times,
            dtype="datetime64[ms]",
        )

        values = np.asarray(
            values,
            dtype=float,
        )

        sensor_temp_arrays[idx] = (
            times,
            values,
        )

        ax_sensor_temp.plot(
            times,
            values,
            color=sensor_colors[idx % len(sensor_colors)],
            label=f"Sensor {idx}",
        )


    ax_sensor_mass.set_ylabel("Mass (g)")
    ax_sensor_mass.set_title("Sensor Mass")
    ax_sensor_mass.legend()


    ax_sensor_temp.set_ylabel("Temperature (°C)")
    ax_sensor_temp.set_title("Sensor Temperature")
    ax_sensor_temp.legend()


    # -------------------------
    # X axis formatting
    # -------------------------

    utc_formatter = DateFormatter(
        "%Y-%m-%dT%H:%M:%SZ",
        tz=timezone.utc,
    )

    locator = AutoDateLocator(
        minticks=10,
        maxticks=20,
    )

    for ax in axes:
        ax.xaxis.set_major_formatter(utc_formatter)
        ax.xaxis.set_major_locator(locator)


    ax_temp.set_xlabel("Time")
    ax_sensor_temp.set_xlabel("Time")


    # -------------------------
    # Plot registry
    # -------------------------

    plot_series = []


    def add_series(name, axis, times, values):

        plot_series.append(
            (
                name,
                axis,
                times,
                values,
            )
        )


    add_series(
        "Aggregate Mass",
        ax_mass,
        timestamps,
        mass,
    )

    add_series(
        "Aggregate Temperature",
        ax_temp,
        timestamps,
        temperature,
    )


    for idx, (times, values) in sensor_mass_arrays.items():
        add_series(
            f"Mass Sensor {idx}",
            ax_sensor_mass,
            times,
            values,
        )


    for idx, (times, values) in sensor_temp_arrays.items():
        add_series(
            f"Temperature Sensor {idx}",
            ax_sensor_temp,
            times,
            values,
        )


    # -------------------------
    # Statistics
    # -------------------------

    def format_stats(values, elapsed):

        values = finite_values(values)


        if len(values):
            mean = np.mean(values)
            median = np.median(values)
            std = np.std(values)
            min_value = np.min(values)
            max_value = np.max(values)
        else:
            mean = 'invalid'
            median = 'invalid'
            std = 'invalid'
            min_value = 'invalid'
            max_value = 'invalid'

        return (
            f"range: {elapsed}\n"
            f"samples: {len(values):8.3f}\n"
            f"min,max: [{min_value:8.3f},{max_value:8.3f}], "
            f"Δ: {max_value - min_value:10.3f}, "
            f"μ: {mean:8.3f}\n"
            f"med: {median:8.3f}, "
            f"1σ/2σ/3σ: {std:8.3f} / {2*std:8.3f} / {3*std:8.3f}"
        )


    stats_boxes = {}

    for ax in axes:
        stats_boxes[ax] = ax.text(
            0.02,
            0.98,
            "",
            transform=ax.transAxes,
            verticalalignment="top",
            fontsize=8,
            family="monospace",
        )


    # -------------------------
    # Helpers
    # -------------------------

    def finite_values(values):
        return values[np.isfinite(values)]

    def visible_range(ax):

        x_min, x_max = ax.get_xlim()

        start = np.datetime64(
            num2date(
                x_min,
                tz=timezone.utc,
            ).replace(tzinfo=None)
        )

        end = np.datetime64(
            num2date(
                x_max,
                tz=timezone.utc,
            ).replace(tzinfo=None)
        )

        return start, end


    busy = False


    def update_view():

        nonlocal busy

        if busy:
            return

        busy = True

        try:

            start, end = visible_range(ax_mass)

            elapsed = int(
                (end - start) /
                np.timedelta64(1, "s")
            )

            elapsed_str = get_elapsed_str(elapsed)

            axis_text = defaultdict(list)
            axis_values = defaultdict(list)


            for name, axis, times, values in plot_series:
                start_idx = np.searchsorted(
                    times,
                    start,
                    side="left",
                )

                end_idx = np.searchsorted(
                    times,
                    end,
                    side="right",
                )

                if start_idx >= end_idx:
                    continue

                visible = values[start_idx:end_idx]
                finite = finite_values(visible)
                if not len(finite):
                    continue

                axis_text[axis].append(
                    f"{name}\n"
                    f"{format_stats(finite, elapsed_str)}"
                )

                axis_values[axis].append(finite)


            for axis, texts in axis_text.items():

                stats_boxes[axis].set_text(
                    "\n\n".join(texts)
                )


            for axis, values in axis_values.items():

                ymin = min(np.min(v) for v in values)

                ymax = max(np.max(v) for v in values)

                span = ymax - ymin

                if span == 0:
                    span = abs(ymin) if ymin else 1

                padding = span * 0.05

                axis.set_ylim(
                    ymin - padding,
                    ymax + padding,
                )


            fig.canvas.draw_idle()


        finally:
            busy = False


    # Update after user finishes interacting
    fig.canvas.mpl_connect(
        "button_release_event",
        lambda event: update_view(),
    )


    update_view()


    fig.autofmt_xdate()

    fig.subplots_adjust(
        left=0.08,
        right=0.98,
        top=0.88,
        bottom=0.08,
        hspace=0.25,
        wspace=0.15,
    )

    plt.show()