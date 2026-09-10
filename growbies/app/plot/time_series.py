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
        device.serial,
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
        dtype='datetime64[ms]',
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

    # -------------------------
    # Aggregate figure
    # -------------------------

    fig_aggregate, (
        ax_mass,
        ax_temp,
    ) = plt.subplots(
        2,
        1,
        figsize=(16, 10),
        sharex=True,
    )

    fig_aggregate.suptitle(
        f'Name: {device_name}\n'
        f'Serial: {device_serial}\n'
        f'Aggregate Data'
    )

    aggregate_axes = [
        ax_mass,
        ax_temp,
    ]

    # -------------------------
    # Aggregate plots
    # -------------------------

    ax_mass.plot(
        timestamps,
        mass,
        color='blue',
    )

    ax_mass.set_ylabel('Mass (g)')
    ax_mass.set_title('Aggregate Mass')

    ax_temp.plot(
        timestamps,
        temperature,
        color='red',
    )

    ax_temp.set_ylabel('Temperature (°C)')
    ax_temp.set_title('Aggregate Temperature')
    ax_temp.set_xlabel('Time')

    # -------------------------
    # Sensor data
    # -------------------------

    sensor_colors = [
        'cyan',
        'magenta',
        'gray',
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
            dtype='datetime64[ms]',
        )

        values = np.asarray(
            values,
            dtype=float,
        )

        sensor_mass_arrays[idx] = (
            times,
            values,
        )

    for idx, (times, values) in sensor_temp_lists.items():

        times = np.asarray(
            times,
            dtype='datetime64[ms]',
        )

        values = np.asarray(
            values,
            dtype=float,
        )

        sensor_temp_arrays[idx] = (
            times,
            values,
        )

    # -------------------------
    # Sensor figure
    # -------------------------

    fig_sensor, (
        ax_sensor_mass,
        ax_sensor_temp,
    ) = plt.subplots(
        2,
        1,
        figsize=(16, 10),
        sharex=True,
    )

    fig_sensor.suptitle(
        f'Name: {device_name}\n'
        f'Serial: {device_serial}\n'
        f'Sensor Data'
    )

    sensor_axes = [
        ax_sensor_mass,
        ax_sensor_temp,
    ]

    # -------------------------
    # Sensor plots
    # -------------------------

    for idx, (times, values) in sensor_mass_arrays.items():

        ax_sensor_mass.plot(
            times,
            values,
            color=sensor_colors[idx % len(sensor_colors)],
            label=f'Sensor {idx}',
        )

    for idx, (times, values) in sensor_temp_arrays.items():

        ax_sensor_temp.plot(
            times,
            values,
            color=sensor_colors[idx % len(sensor_colors)],
            label=f'Sensor {idx}',
        )

    ax_sensor_mass.set_ylabel('Mass (g)')
    ax_sensor_mass.set_title('Sensor Mass')
    ax_sensor_mass.legend()

    ax_sensor_temp.set_ylabel('Temperature (°C)')
    ax_sensor_temp.set_title('Sensor Temperature')
    ax_sensor_temp.set_xlabel('Time')
    ax_sensor_temp.legend()

    # -------------------------
    # X axis formatting
    # -------------------------

    utc_formatter = DateFormatter(
        '%Y-%m-%dT%H:%M:%SZ',
        tz=timezone.utc,
    )

    locator = AutoDateLocator(
        minticks=10,
        maxticks=20,
    )

    for ax in aggregate_axes + sensor_axes:
        ax.xaxis.set_major_formatter(utc_formatter)
        ax.xaxis.set_major_locator(locator)

    # -------------------------
    # Plot registry
    # -------------------------

    aggregate_series = []

    aggregate_series.append(
        (
            'Aggregate Mass',
            ax_mass,
            timestamps,
            mass,
        )
    )

    aggregate_series.append(
        (
            'Aggregate Temperature',
            ax_temp,
            timestamps,
            temperature,
        )
    )

    sensor_series = []

    for idx, (times, values) in sensor_mass_arrays.items():
        sensor_series.append(
            (
                f'Mass Sensor {idx}',
                ax_sensor_mass,
                times,
                values,
            )
        )

    for idx, (times, values) in sensor_temp_arrays.items():
        sensor_series.append(
            (
                f'Temperature Sensor {idx}',
                ax_sensor_temp,
                times,
                values,
            )
        )

    # -------------------------
    # Statistics
    # -------------------------

    def finite_values(values):
        return values[np.isfinite(values)]

    def format_stats(values, elapsed):

        values = finite_values(values)

        if len(values):
            mean = np.mean(values)
            median = np.median(values)
            std = np.std(values)
            min_value = np.min(values)
            max_value = np.max(values)
        else:
            mean = median = std = min_value = max_value = np.nan

        delta = max_value - min_value

        return (
            f'{"samples":<10} {"range":<20}\n'
            f'{len(values):<10d} {elapsed:<20}\n'
            f'{"min":<10} {"max":<10} {"Δ":<10} '
            f'{"μ":<10} {"med":<10}\n'
            f'{min_value:<10.3f} {max_value:<10.3f} '
            f'{delta:<10.3f} {mean:<10.3f} {median:<10.3f}\n'
            f'{"1σ":<10} {"2σ":<10} {"3σ":<10}\n'
            f'{std:<10.3f} {2 * std:<10.3f} {3 * std:<10.3f}'
        )

    aggregate_stats_boxes = {}

    for ax in aggregate_axes:
        aggregate_stats_boxes[ax] = ax.text(
            0.02,
            0.98,
            '',
            transform=ax.transAxes,
            verticalalignment='top',
            fontsize=8,
            family='monospace',
        )

    sensor_stats_boxes = {}

    for ax in sensor_axes:
        sensor_stats_boxes[ax] = ax.text(
            0.02,
            0.98,
            '',
            transform=ax.transAxes,
            verticalalignment='top',
            fontsize=8,
            family='monospace',
        )

    # -------------------------
    # Helpers
    # -------------------------

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

    # -------------------------
    # Aggregate update
    # -------------------------

    aggregate_busy = False

    def update_aggregate_view(autoscale_y=True):

        nonlocal aggregate_busy

        if aggregate_busy:
            return

        aggregate_busy = True

        try:

            start, end = visible_range(ax_mass)

            elapsed = int(
                (end - start) /
                np.timedelta64(1, 's')
            )

            elapsed_str = get_elapsed_str(elapsed)

            axis_text = defaultdict(list)
            axis_values = defaultdict(list)

            for name, axis, times, values in aggregate_series:

                start_idx = np.searchsorted(
                    times,
                    start,
                    side='left',
                )

                end_idx = np.searchsorted(
                    times,
                    end,
                    side='right',
                )

                if start_idx >= end_idx:
                    continue

                visible = values[start_idx:end_idx]
                finite = finite_values(visible)

                if not len(finite):
                    continue

                axis_text[axis].append(
                    f'{name}\n'
                    f'{format_stats(finite, elapsed_str)}'
                )

                axis_values[axis].append(finite)

            for axis, texts in axis_text.items():
                aggregate_stats_boxes[axis].set_text(
                    '\n\n'.join(texts)
                )

            if autoscale_y:
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

            fig_aggregate.canvas.draw_idle()

        finally:
            aggregate_busy = False

    # -------------------------
    # Sensor update
    # -------------------------

    sensor_busy = False

    def update_sensor_view(autoscale_y=True):

        nonlocal sensor_busy

        if sensor_busy:
            return

        sensor_busy = True

        try:

            start, end = visible_range(ax_sensor_mass)

            elapsed = int(
                (end - start) /
                np.timedelta64(1, 's')
            )

            elapsed_str = get_elapsed_str(elapsed)

            axis_text = defaultdict(list)
            axis_values = defaultdict(list)

            for name, axis, times, values in sensor_series:

                start_idx = np.searchsorted(
                    times,
                    start,
                    side='left',
                )

                end_idx = np.searchsorted(
                    times,
                    end,
                    side='right',
                )

                if start_idx >= end_idx:
                    continue

                visible = values[start_idx:end_idx]
                finite = finite_values(visible)

                if not len(finite):
                    continue

                axis_text[axis].append(
                    f'{name}\n'
                    f'{format_stats(finite, elapsed_str)}'
                )

                axis_values[axis].append(finite)

            for axis, texts in axis_text.items():
                sensor_stats_boxes[axis].set_text(
                    '\n\n'.join(texts)
                )

            if autoscale_y:
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

            fig_sensor.canvas.draw_idle()

        finally:
            sensor_busy = False

    # -------------------------
    # Update after interaction
    # -------------------------

    aggregate_press_limits = None
    sensor_press_limits = None

    def on_aggregate_press(event):

        nonlocal aggregate_press_limits

        if event.inaxes in aggregate_axes:
            aggregate_press_limits = (
                event.inaxes.get_xlim(),
                event.inaxes.get_ylim(),
            )

    def on_sensor_press(event):

        nonlocal sensor_press_limits

        if event.inaxes in sensor_axes:
            sensor_press_limits = (
                event.inaxes.get_xlim(),
                event.inaxes.get_ylim(),
            )

    def on_aggregate_release(event):

        nonlocal aggregate_press_limits

        if aggregate_press_limits is None:
            return

        old_xlim, old_ylim = aggregate_press_limits
        aggregate_press_limits = None

        if event.inaxes not in aggregate_axes:
            return

        new_xlim = event.inaxes.get_xlim()
        new_ylim = event.inaxes.get_ylim()

        x_changed = not np.allclose(old_xlim, new_xlim)
        y_changed = not np.allclose(old_ylim, new_ylim)

        if x_changed:
            update_aggregate_view(
                autoscale_y=not y_changed,
            )

    def on_sensor_release(event):

        nonlocal sensor_press_limits

        if sensor_press_limits is None:
            return

        old_xlim, old_ylim = sensor_press_limits
        sensor_press_limits = None

        if event.inaxes not in sensor_axes:
            return

        new_xlim = event.inaxes.get_xlim()
        new_ylim = event.inaxes.get_ylim()

        x_changed = not np.allclose(old_xlim, new_xlim)
        y_changed = not np.allclose(old_ylim, new_ylim)

        if x_changed:
            update_sensor_view(
                autoscale_y=not y_changed,
            )

    fig_aggregate.canvas.mpl_connect(
        'button_press_event',
        on_aggregate_press,
    )

    fig_aggregate.canvas.mpl_connect(
        'button_release_event',
        on_aggregate_release,
    )

    fig_sensor.canvas.mpl_connect(
        'button_press_event',
        on_sensor_press,
    )

    fig_sensor.canvas.mpl_connect(
        'button_release_event',
        on_sensor_release,
    )

    update_aggregate_view()
    update_sensor_view()

    # -------------------------
    # Layout
    # -------------------------

    fig_aggregate.autofmt_xdate()

    fig_aggregate.subplots_adjust(
        left=0.08,
        right=0.98,
        top=0.88,
        bottom=0.13,
        hspace=0.25,
    )

    fig_sensor.autofmt_xdate()

    fig_sensor.subplots_adjust(
        left=0.08,
        right=0.98,
        top=0.88,
        bottom=0.13,
        hspace=0.25,
    )

    plt.show()
