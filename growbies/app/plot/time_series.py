from collections import defaultdict
from datetime import datetime, timezone
from typing import Iterator

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.dates import AutoDateLocator, DateFormatter, num2date
from sqlalchemy.engine.row import Row

from growbies.common.utils.timestamp import get_elapsed_str
from growbies.db.engine import get_db_engine


FIGURE_SIZE = (16, 10)

SENSOR_COLORS = [
    'cyan',
    'magenta',
    'gray',
]


def plot_time_series(
        fuzzy_id: str,
        start_time: datetime,
        end_time: datetime,
):
    db_engine = get_db_engine()
    device = db_engine.device.get(fuzzy_id)

    datapoints, mass_sensor_datapoints, temp_sensor_datapoints = \
        db_engine.datapoint.get_device_datapoints(
            device.id,
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

def _valid_tare_idx() -> Iterator[int]:
    yield from (0, 1, 2)

def _get_tare_idx_name(idx: int):
    if idx in _valid_tare_idx():
        return f'Tare {chr(ord("A") + idx)}'
    else:
        return 'Unknown'

def _plot_time_series(
        datapoints: list[Row],
        mass_sensor_datapoints: list[Row],
        temp_sensor_datapoints: list[Row],
        device_name: str,
        device_serial: str,
):
    timestamps, mass, temperature, tare_masses = \
        _prepare_aggregate_data(
            datapoints,
        )

    sensor_mass = _prepare_sensor_data(
        mass_sensor_datapoints,
        'mass',
    )

    sensor_temperature = _prepare_sensor_data(
        temp_sensor_datapoints,
        'temperature',
    )

    _create_aggregate_figure(
        timestamps,
        mass,
        temperature,
        tare_masses,
        device_name,
        device_serial,
    )

    _create_sensor_figure(
        sensor_mass,
        sensor_temperature,
        device_name,
        device_serial,
    )

    plt.show()


# ----------------------------------------------------------------------
# Data preparation
# ----------------------------------------------------------------------


def _prepare_aggregate_data(datapoints):
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

    tare_values = np.asarray(
        [dp.tare_values for dp in datapoints],
        dtype=float,
    )

    tare_masses = mass[:, np.newaxis] - tare_values

    return (
        timestamps,
        mass,
        temperature,
        tare_masses,
    )


def _prepare_sensor_data(rows, value_attribute):
    sensor_data = defaultdict(lambda: ([], []))

    for row in rows:
        sensor_data[row.idx][0].append(row.timestamp)
        sensor_data[row.idx][1].append(
            getattr(row, value_attribute),
        )

    result = {}

    for idx, (times, values) in sensor_data.items():
        result[idx] = (
            np.asarray(
                times,
                dtype='datetime64[ms]',
            ),
            np.asarray(
                values,
                dtype=float,
            ),
        )

    return result


# ----------------------------------------------------------------------
# Figure creation
# ----------------------------------------------------------------------


def _create_aggregate_figure(
        timestamps,
        mass,
        temperature,
        tare_masses,
        device_name,
        device_serial,
):
    fig, (ax_mass, ax_temperature) = plt.subplots(
        2,
        1,
        figsize=FIGURE_SIZE,
        sharex=True,
    )

    fig.suptitle(
        f'Name: {device_name}\n'
        f'Serial: {device_serial}\n'
    )

    mass_lines = []

    mass_lines.append(
        ax_mass.plot(
            timestamps,
            mass,
            color='black',
            linestyle='--',
            alpha=0.5,
            label='Aggregate Mass',
        )[0]
    )

    for idx in _valid_tare_idx():
        if idx >= tare_masses.shape[1]:
            continue

        mass_lines.append(
            ax_mass.plot(
                timestamps,
                tare_masses[:, idx],
                label=_get_tare_idx_name(idx),
            )[0]
        )

    ax_mass.set_ylabel('Mass (g)')
    ax_mass.set_title('Mass')

    legend = ax_mass.legend(loc='best')

    for legend_line, plot_line in zip(
            legend.get_lines(),
            mass_lines,
    ):
        legend_line.set_picker(True)
        legend_line._plot_line = plot_line

    temperature_line = ax_temperature.plot(
        timestamps,
        temperature,
        color='red',
    )[0]

    ax_temperature.set_ylabel('Temperature (°C)')
    ax_temperature.set_title('Temperature')
    ax_temperature.set_xlabel('Time')

    axes = [
        ax_mass,
        ax_temperature,
    ]

    series = [
        (
            'Aggregate Mass',
            ax_mass,
            timestamps,
            mass,
            mass_lines[0],
        ),
    ]

    for idx in _valid_tare_idx():
        if idx >= tare_masses.shape[1]:
            continue

        series.append(
            (
                _get_tare_idx_name(idx),
                ax_mass,
                timestamps,
                tare_masses[:, idx],
                mass_lines[idx + 1],
            )
        )

    series.append(
        (
            'Temperature',
            ax_temperature,
            timestamps,
            temperature,
            temperature_line,
        )
    )

    _configure_figure(
        fig,
        axes,
    )

    stats_boxes = _create_stats_boxes(
        axes,
    )

    _install_interaction(
        fig,
        axes,
        ax_mass,
        series,
        stats_boxes,
    )


def _create_sensor_figure(
        sensor_mass,
        sensor_temperature,
        device_name,
        device_serial,
):
    fig, (ax_mass, ax_temperature) = plt.subplots(
        2,
        1,
        figsize=FIGURE_SIZE,
        sharex=True,
    )

    fig.suptitle(
        f'Name: {device_name}\n'
        f'Serial: {device_serial}\n'
        f'Sensor Data'
    )

    mass_series = _plot_sensor_series(
        ax_mass,
        sensor_mass,
        'Mass Sensor',
    )

    temperature_series = _plot_sensor_series(
        ax_temperature,
        sensor_temperature,
        'Temperature Sensor',
    )

    ax_mass.set_ylabel('Mass (g)')
    ax_mass.set_title('Sensor Mass')

    ax_temperature.set_ylabel('Temperature (°C)')
    ax_temperature.set_title('Sensor Temperature')
    ax_temperature.set_xlabel('Time')

    if mass_series:
        ax_mass.legend()

    if temperature_series:
        ax_temperature.legend()

    axes = [
        ax_mass,
        ax_temperature,
    ]

    series = mass_series + temperature_series

    _configure_figure(
        fig,
        axes,
    )

    stats_boxes = _create_stats_boxes(
        axes,
    )

    _install_interaction(
        fig,
        axes,
        ax_mass,
        series,
        stats_boxes,
    )


def _plot_sensor_series(
        ax,
        sensor_data,
        name_prefix,
):
    series = []

    for idx, (times, values) in sensor_data.items():
        ax.plot(
            times,
            values,
            color=SENSOR_COLORS[
                idx % len(SENSOR_COLORS)
            ],
            label=f'Sensor {idx}',
        )

        series.append(
            (
                f'{name_prefix} {idx}',
                ax,
                times,
                values,
            )
        )

    return series


# ----------------------------------------------------------------------
# Figure configuration
# ----------------------------------------------------------------------


def _configure_figure(fig, axes):
    formatter = DateFormatter(
        '%Y-%m-%dT%H:%M:%SZ',
        tz=timezone.utc,
    )

    locator = AutoDateLocator(
        minticks=10,
        maxticks=20,
    )

    for ax in axes:
        ax.xaxis.set_major_formatter(
            formatter,
        )
        ax.xaxis.set_major_locator(
            locator,
        )

    fig.autofmt_xdate()

    fig.subplots_adjust(
        left=0.08,
        right=0.98,
        top=0.88,
        bottom=0.13,
        hspace=0.25,
    )


# ----------------------------------------------------------------------
# Statistics
# ----------------------------------------------------------------------


def _finite_values(values):
    return values[np.isfinite(values)]


def _format_stats(values, elapsed):
    values = _finite_values(values)

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


def _create_stats_boxes(axes):
    stats_boxes = {}

    for ax in axes:
        stats_boxes[ax] = ax.text(
            0.02,
            0.98,
            '',
            transform=ax.transAxes,
            verticalalignment='top',
            fontsize=8,
            family='monospace',
        )

    return stats_boxes


# ----------------------------------------------------------------------
# View handling
# ----------------------------------------------------------------------


def _visible_range(ax):
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


def _update_view(
        fig,
        x_axis,
        series,
        stats_boxes,
        autoscale_y=True,
):
    start, end = _visible_range(
        x_axis,
    )

    elapsed = int(
        (end - start) /
        np.timedelta64(1, 's')
    )

    elapsed_str = get_elapsed_str(
        elapsed,
    )

    axis_text = defaultdict(list)
    axis_values = defaultdict(list)

    for item in series:
        if len(item) == 5:
            name, axis, times, values, plot_line = item

            if not plot_line.get_visible():
                continue
        else:
            name, axis, times, values = item

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

        visible = values[
            start_idx:end_idx
        ]

        finite = _finite_values(
            visible,
        )

        if not len(finite):
            continue

        axis_text[axis].append(
            f'{name}\n'
            f'{_format_stats(finite, elapsed_str)}'
        )

        axis_values[axis].append(
            finite,
        )

    # Clear all statistics first so that an axis with no visible
    # finite data does not retain stale statistics.
    for box in stats_boxes.values():
        box.set_text('')

    for axis, texts in axis_text.items():
        stats_boxes[axis].set_text(
            '\n\n'.join(texts),
        )

    if autoscale_y:
        for axis, values in axis_values.items():
            ymin = min(
                np.min(values)
                for values in values
            )

            ymax = max(
                np.max(values)
                for values in values
            )

            span = ymax - ymin

            if span == 0:
                span = abs(ymin) if ymin else 1

            padding = span * 0.05

            axis.set_ylim(
                ymin - padding,
                ymax + padding,
            )

    fig.canvas.draw_idle()


# ----------------------------------------------------------------------
# Interaction
# ----------------------------------------------------------------------


def _install_interaction(
        fig,
        axes,
        x_axis,
        series,
        stats_boxes,
):
    press_limits = None
    busy = False

    def update(autoscale_y=True):
        nonlocal busy

        if busy:
            return

        busy = True

        try:
            _update_view(
                fig,
                x_axis,
                series,
                stats_boxes,
                autoscale_y=autoscale_y,
            )
        finally:
            busy = False

    def on_press(event):
        nonlocal press_limits

        if event.inaxes not in axes:
            return

        press_limits = (
            event.inaxes.get_xlim(),
            event.inaxes.get_ylim(),
        )

    def on_release(event):
        nonlocal press_limits

        if press_limits is None:
            return

        old_xlim, old_ylim = press_limits
        press_limits = None

        if event.inaxes not in axes:
            return

        new_xlim = event.inaxes.get_xlim()
        new_ylim = event.inaxes.get_ylim()

        x_changed = not np.allclose(
            old_xlim,
            new_xlim,
        )

        y_changed = not np.allclose(
            old_ylim,
            new_ylim,
        )

        if not x_changed:
            return

        update(
            autoscale_y=not y_changed,
        )

    def on_pick(event):
        legend_line = event.artist

        if not hasattr(
                legend_line,
                '_plot_line',
        ):
            return

        plot_line = legend_line._plot_line

        visible = not plot_line.get_visible()

        plot_line.set_visible(visible)

        legend_line.set_alpha(
            1.0 if visible else 0.3,
        )

        update()

    fig.canvas.mpl_connect(
        'button_press_event',
        on_press,
    )

    fig.canvas.mpl_connect(
        'button_release_event',
        on_release,
    )

    fig.canvas.mpl_connect(
        'pick_event',
        on_pick,
    )

    update()
