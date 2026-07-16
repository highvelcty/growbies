from argparse import Namespace
from typing import Optional
import logging
import numpy as np
import sys

from matplotlib.dates import AutoDateLocator, DateFormatter, num2date
from sqlalchemy.engine.row import Row
import matplotlib.pyplot as plt

from growbies.db.models.datapoint import DataPoints
from .cli import Action, PlotAction
from growbies.cli.common import Param as CommonParam
from growbies.db.engine import get_db_engine
from growbies.db.models.session import Session
from growbies.protocol.common.calibration import REF_TEMPERATURE_C
from growbies.service.common import ServiceCmdError
from growbies.utils.report import short_uuid
from growbies.utils.timestamp import FMT_DT_INT, get_elapsed_str

logger = logging.getLogger(__name__)

def execute(args: Namespace):
    returncode = 0

    fuzzy_id = getattr(args, CommonParam.FUZZY_ID)
    plot_type = getattr(args, Action.PLOT)

    if plot_type == PlotAction.MASS:
        plot_mass_cal(fuzzy_id)
    elif plot_type == PlotAction.TEMP:
        plot_temp_cal(fuzzy_id)
    elif plot_type == PlotAction.TIME:
        plot_time(fuzzy_id)

    if returncode == 0:
        logger.info('*** PASS ***')
    else:
        logger.error('*** FAIL ***')

    sys.exit(returncode)

def plot_mass_vs_time(session: Session):
    engine = get_db_engine().session
    tare_engine = get_db_engine().tare
    datapoints = engine.get_datapoints(session.id)

    if not datapoints:
        raise ServiceCmdError(f"No datapoints found for session {session.id}")

    # ---- Extract main mass ----
    timestamps = list()
    mass_values = list()
    for dp in datapoints:
        tare_val = tare_engine.get(dp.tare_id).values[1]
        timestamps.append(dp.timestamp)
        mass_values.append(dp.mass - tare_val)

    # ---- Extract per-sensor mass ----
    max_sensors = len(datapoints[0].mass_sensors)

    sensor_traces = [[] for _ in range(max_sensors)]

    for dp in datapoints:
        sensors_sorted = sorted(dp.mass_sensors, key=lambda s: s.idx)
        for i in range(max_sensors):
            if i < len(sensors_sorted):
                sensor_traces[i].append(sensors_sorted[i].mass)
            else:
                sensor_traces[i].append(None)

    # ---- Temperature ----
    temperature_values = [dp.temperature for dp in datapoints]

    # ---- Plot ----
    fig, ax_mass = plt.subplots()

    # Aggregate mass line + dots
    ax_mass.plot(timestamps, mass_values, label="Aggregate Mass", linewidth=1, marker='.')
    # ax_mass.scatter(timestamps, mass_values, alpha=0.7, marker='.')

    # Per-sensor lines + dots
    for i in range(max_sensors):
        ax_mass.plot(timestamps, sensor_traces[i], label=f"Sensor {i} mass", marker='.', alpha=.25)
        # ax_mass.scatter(timestamps, sensor_traces[i], alpha=0.7, marker = '.')

    ax_mass.set_ylabel("Mass (g)")
    ax_mass.set_xlabel("Time")
    ax_mass.legend(loc="upper left")
    ax_mass.set_title(f"Mass & Temperature session {session.name}")

    # Right y-axis: Temperature
    ax_temp = ax_mass.twinx()
    ax_temp.plot(timestamps, temperature_values, label="Temperature", color="purple",
                 marker='.', linewidth=1, alpha=.25)
    # ax_temp.scatter(timestamps, temperature_values, color="tab:red", alpha=0.7, marker='.')
    ax_temp.set_ylabel("Temperature (°C)")
    ax_temp.legend(loc="upper right")

    # Format x-axis
    ax_mass.xaxis.set_major_formatter(DateFormatter(FMT_DT_INT))
    fig.autofmt_xdate()
    plt.tight_layout()
    plt.show()

def plot_ref_mass_vs_temperature(session: Session):
    engine = get_db_engine().session
    datapoints = engine.get_datapoints(session.id)

    if not datapoints:
        raise ServiceCmdError(f"No datapoints found for session {session.id}")

    # ---- Extract temperature ----
    temperature_values = [dp.temperature for dp in datapoints]

    # ---- Determine number of sensors ----
    max_sensors = len(datapoints[0].mass_sensors)

    # ---- Prepare actual mass and reference mass per sensor ----
    sensor_mass_traces = [[] for _ in range(max_sensors)]
    sensor_ref_traces = [[] for _ in range(max_sensors)]
    sensor_temp_traces = [[] for _ in range(max_sensors)]  # temperature for points with ref_mass

    for dp in datapoints:
        sensors_sorted = sorted(dp.mass_sensors, key=lambda s: s.idx)
        for i in range(max_sensors):
            sensor = sensors_sorted[i] if i < len(sensors_sorted) else None
            if sensor and sensor.ref_mass is not None:
                # Only include measured mass if there is a reference mass
                sensor_mass_traces[i].append(sensor.mass)
                sensor_ref_traces[i].append(sensor.ref_mass)
                sensor_temp_traces[i].append(dp.temperature)

    # ---- Plotting ----
    fig, ax_mass = plt.subplots()

    # Left y-axis: actual sensor mass (triangles)
    for i in range(max_sensors):
        if sensor_mass_traces[i]:
            ax_mass.scatter(
                sensor_temp_traces[i],
                sensor_mass_traces[i],
                label=f"Sensor {i} mass",
                marker="^",
                alpha=0.7
            )
    ax_mass.set_xlabel("Temperature (°C)")
    ax_mass.set_ylabel("Measured Mass (g)")
    ax_mass.set_title(f"Sensor Mass vs Reference Mass for session {session.name}")

    # Right y-axis: reference mass (circles)
    ax_ref = ax_mass.twinx()
    for i in range(max_sensors):
        if sensor_ref_traces[i]:
            ax_ref.scatter(
                sensor_temp_traces[i],
                sensor_ref_traces[i],
                label=f"Sensor {i} ref mass",
                marker="o",
                alpha=0.5,
                color=f"C{i}"
            )
    ax_ref.set_ylabel("Reference Mass (g)")

    # ---- Separate legends ----
    legend_mass = ax_mass.legend(loc="upper left", title="Measured Mass")
    legend_ref = ax_ref.legend(loc="upper right", title="Reference Mass")

    ax_mass.add_artist(legend_mass)  # Ensure both legends show

    plt.tight_layout()
    plt.show()

def plot_mass_vs_temp(session: "Session"):
    """
    Plot aggregate mass and per-sensor mass vs temperature
    on a single set of axes, color-coded with a legend.
    """
    engine = get_db_engine().session
    datapoints = engine.get_datapoints(session.id)

    if not datapoints:
        raise ServiceCmdError(f"No datapoints found for session {session.id}")

    max_sensors = len(datapoints[0].mass_sensors)

    # ---- Collect aggregate data ----
    temps = []
    aggregate_mass = []

    for dp in datapoints:
        temps.append(dp.temperature)
        aggregate_mass.append(dp.mass)

    temps = np.array(temps)
    aggregate_mass = np.array(aggregate_mass)

    # ---- Plot ----
    plt.figure(figsize=(8, 6))

    # Aggregate mass
    plt.plot(
        temps,
        aggregate_mass,
        linewidth=2,
        label="Aggregate Mass"
    )

    # Per-sensor mass
    for sensor_idx in range(max_sensors):
        sensor_mass = []

        for dp in datapoints:
            if sensor_idx < len(dp.mass_sensors):
                sensor_mass.append(dp.mass_sensors[sensor_idx].mass)

        sensor_mass = np.array(sensor_mass)

        plt.plot(
            temps,
            sensor_mass,
            linestyle='--',
            alpha=0.8,
            label=f"Sensor {sensor_idx}"
        )

    plt.xlabel("Temperature (°C)")
    plt.ylabel("Mass (g)")
    plt.title("Aggregate and Per-Sensor Mass vs Temperature")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()


def plot_mass_cal(fuzzy_id: str):
    session = get_db_engine().session.get(fuzzy_id)
    mad_k_val = 7

    engine = get_db_engine().session
    datapoints = engine.get_datapoints(session.id)

    if not datapoints:
        raise ServiceCmdError(f"No datapoints found for session {session.id}")

    max_sensors = len(datapoints[0].mass_sensors)

    for sensor_idx in range(max_sensors):
        timestamps, masses, ref_masses, temps = _extract_from_datapoints(datapoints, sensor_idx)

        # --- Sort by reference mass (for plotting continuity only) ---
        sort_idx = np.argsort(ref_masses)
        ref_mass_sorted = ref_masses[sort_idx]
        adc_sorted = masses[sort_idx]

        # --- Group by reference mass ---
        unique_masses = np.unique(ref_masses)
        grouped_adc = []
        grouped_ref = []
        for m in unique_masses:
            mask = ref_masses == m  # select all points with this reference mass
            adc_group = masses[mask]  # ADC values in this group
            ref_group = ref_masses[mask]  # all equal to m
            grouped_adc.append(adc_group)
            grouped_ref.append(ref_group)

        # --- MAD filtering per reference mass group ---
        adc_kept = []  # ADC points kept after MAD (for fitting / green dots)
        ref_kept = []  # corresponding reference masses
        adc_filtered = []  # ADC points rejected by MAD (for red X)
        ref_filtered = []  # corresponding reference masses

        for adc_group, ref_group in zip(grouped_adc, grouped_ref):
            mask_keep = _mad_filter(adc_group, k=mad_k_val)

            # Keep points
            adc_kept.append(adc_group[mask_keep])
            ref_kept.append(ref_group[mask_keep])

            # Filtered (outliers)
            adc_filtered.append(adc_group[~mask_keep])
            ref_filtered.append(ref_group[~mask_keep])

        # Flatten lists for later plotting
        adc_kept = np.concatenate(adc_kept)
        ref_kept = np.concatenate(ref_kept)
        adc_filtered = np.concatenate(adc_filtered)
        ref_filtered = np.concatenate(ref_filtered)

        # ============================================================
        # CALIBRATION MODEL
        #
        # We fit:
        #   ref_mass (g) = a0 + a1 * ADC + a2 * ADC^2
        #
        # This matches firmware usage EXACTLY.
        # ============================================================
        # To view the unfiltered
        #
        # X = np.vstack([
        #     np.ones_like(adc_sorted),
        #     adc_sorted,
        #     adc_sorted ** 2
        # ]).T
        #
        # coeffs, residuals, rank, s = np.linalg.lstsq(X, ref_mass_sorted, rcond=None)

        X = np.vstack([
            np.ones_like(adc_kept),
            adc_kept,
            adc_kept ** 2
        ]).T

        coeffs, residuals, rank, s = np.linalg.lstsq(X, ref_kept, rcond=None)

        a0, a1, a2 = coeffs

        # Predicted mass (grams) from ADC
        mass_pred = a0 + a1 * adc_sorted + a2 * adc_sorted ** 2

        # Residuals in grams
        residuals_array = ref_mass_sorted - mass_pred

        # Error statistics (grams)
        rmse = np.sqrt(np.mean(residuals_array ** 2))
        sigma1 = np.std(residuals_array, ddof=1)
        sigma2 = 2 * sigma1
        sigma3 = 3 * sigma1

        # ============================================================
        # PLOTTING
        # ============================================================
        fig, (ax_time, ax_ref) = plt.subplots(2, 1, figsize=(12, 10))

        # --- Subplot 1: ADC & Temperature vs Time ---
        ax1 = ax_time
        ax1.plot(timestamps, masses, 'b.-', label='ADC Reading')
        ax1.set_xlabel('Timestamp')
        ax1.set_ylabel('ADC', color='tab:blue')
        ax1.tick_params(axis='y', labelcolor='tab:blue')

        ax2 = ax1.twinx()
        ax2.plot(timestamps, temps, 'r.-', label='Temp (°C)')
        ax2.set_ylabel('Temperature (°C)', color='tab:red')
        ax2.tick_params(axis='y', labelcolor='tab:red')

        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='best')
        ax1.set_title(f'Sensor {sensor_idx} - ADC & Temp vs Timestamp')

        # --- Subplot 2: Predicted Mass vs Reference Mass ---
        ax3 = ax_ref
        ax3.plot(ref_mass_sorted, mass_pred, 'g.-', label='Predicted Mass')
        ax3.plot(ref_mass_sorted, ref_mass_sorted, 'k--', label='Ideal (y=x)')
        ax3.set_xlabel('Reference Mass (g)')
        ax3.set_ylabel('Predicted Mass (g)')
        ax3.grid(True)

        # Residuals on secondary axis
        ax4 = ax3.twinx()
        ax4.plot(ref_mass_sorted, residuals_array, 'm.-', label='Residuals (g)')

        # --- Plot MAD filtered points ---
        if len(ref_filtered) > 0:
            # Predicted mass of filtered points
            mass_pred_filtered = a0 + a1 * adc_filtered + a2 * adc_filtered ** 2
            residual_filtered = ref_filtered - mass_pred_filtered

            # Red X on predicted mass and residual plot with combined legend
            ax3.scatter(ref_filtered, mass_pred_filtered, color='red', marker='x', s=50,
                        label=f'MAD outlier (k={mad_k_val})')
            ax4.scatter(ref_filtered, residual_filtered, color='red', marker='x', s=50)

        for s, style in zip([sigma1, sigma2, sigma3], ['--', ':', '-.']):
            ax4.axhline(s, color='gray', linestyle=style, linewidth=0.8)
            ax4.axhline(-s, color='gray', linestyle=style, linewidth=0.8)
        ax4.set_ylabel('Residuals (g)', color='magenta')
        ax4.tick_params(axis='y', labelcolor='magenta')

        lines3, labels3 = ax3.get_legend_handles_labels()
        lines4, labels4 = ax4.get_legend_handles_labels()
        ax3.legend(lines3 + lines4, labels3 + labels4, loc='best')

        coeff_text = (
            f"M = {a0:.3f} + {a1:.6f}·ADC + {a2:.9f}·ADC²\n"
            f"RMSE = {rmse:.3f} g\n"
            f"σ = {sigma1:.3f} g  |  2σ = {sigma2:.3f} g  |  3σ = {sigma3:.3f} g"
        )
        ax3.text(
            0.02, 0.95, coeff_text,
            transform=ax3.transAxes,
            fontsize=10,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8)
        )

        ax3.set_title(
            f'Sensor {sensor_idx} - Mass Calibration\n'
            f'Model: Mass(g) = a0 + a1·ADC + a2·ADC²'
        )

        fig.tight_layout()
        plt.show()

def _plot_temp_cal(session: "Session", datapoints: DataPoints, sensor_idx: Optional[int] = None):
    filter_threshold_grams = 100
    timestamps, masses, ref_masses, temps = _extract_from_datapoints(datapoints, sensor_idx)
    #
    # outf = open('/home/meyer/tmp/data.csv', 'w')
    # outf.write(f'timestamp,temperature,ref_mass,mass,sensor_0_ref,sensor_0,sensor_1_ref,sensor_1,'
    #            f'sensor_2_ref,sensor_2\n')
    # for datapoint in datapoints:
    #     outf.write(f'{datapoint.timestamp},'
    #                f'{datapoint.temperature},{datapoint.ref_mass},{datapoint.mass},'
    #                f'{datapoint.mass_sensors[0].ref_mass},{datapoint.mass_sensors[0].mass},'
    #                f'{datapoint.mass_sensors[1].ref_mass},{datapoint.mass_sensors[1].mass},'
    #                f'{datapoint.mass_sensors[2].ref_mass},{datapoint.mass_sensors[2].mass}\n')
    # outf.close()

    # ------------------------------------------------------------------
    # DC offset removal (AGGREGATE ONLY, BEFORE EVERYTHING)
    # ------------------------------------------------------------------
    median_offset = 0.0

    if sensor_idx is None:
        # global aggregate bias estimate
        median_offset = np.median(masses - ref_masses)

        # apply correction immediately (this is now the "true" signal forward)
        masses = masses - median_offset

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    fig = plt.figure(figsize=(14, 10))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.4, 1.0], width_ratios=[2.5, 1.5])

    ax_mass_temp = fig.add_subplot(gs[0, :])
    ax_time = fig.add_subplot(gs[1, 0])
    ax_stats = fig.add_subplot(gs[1, 1])

    delta_T = temps - REF_TEMPERATURE_C
    if len(delta_T) < 4:
        raise ServiceCmdError(
            f"Sensor {sensor_idx}: insufficient datapoints for fitting"
        )

    # ------------------------------------------------------------------
    # Filter datapoints using MAD
    # ------------------------------------------------------------------
    raw_error = masses - ref_masses

    median_error = np.median(raw_error)
    mad = np.median(np.abs(raw_error - median_error))

    if mad == 0:
        modified_z = np.zeros_like(raw_error)
    else:
        # A scaling constant that makes the MAD-based z-score comparable to a staandard z-score,
        # when the underlying data is normally distributed.
        modified_z = 0.6745 * (raw_error - median_error) / mad

    mad_threshold = 50

    bad_mask = np.abs(modified_z) > mad_threshold
    good_mask = ~bad_mask

    positive_outlier_mask = bad_mask & (raw_error > median_error)
    negative_outlier_mask = bad_mask & (raw_error < median_error)

    filtered_count = np.count_nonzero(bad_mask)
    total_count = len(masses)
    used_count = total_count - filtered_count

    if used_count < 4:
        raise ServiceCmdError(
            f"Sensor {sensor_idx}: insufficient valid datapoints "
            f"after filtering ({used_count} remaining)"
        )

    # ------------------------------------------------------------------
    # Mass vs ΔT
    # ------------------------------------------------------------------
    delta_T_good = delta_T[good_mask]
    masses_good = masses[good_mask]
    ref_good = ref_masses[good_mask]

    idx = np.argsort(delta_T_good)
    x = delta_T_good[idx]
    y = masses_good[idx]
    ref_sorted = ref_good[idx]

    # Fits
    b0, b1, res_l = _linear_fit(x, y)
    a0, a1, a2, res_q = _quadratic_fit(x, y)
    c0, c1, c2, c3, res_c = _cubic_fit(x, y)

    y_l = b0 + b1 * x
    y_q = a0 + a1 * x + a2 * x ** 2
    y_c = c0 + c1 * x + c2 * x ** 2 + c3 * x ** 3

    # ------------------------------------------------------------------
    # Plot
    # ------------------------------------------------------------------
    # Good datapoints used for fitting
    ax_mass_temp.plot(x, y, 'b.', alpha=0.5, label='Mass (g)')
    # Show accepted/rejected samples at y=0 so they don't affect scaling
    ax_mass_temp.plot(
        delta_T[positive_outlier_mask],
        np.zeros(np.count_nonzero(positive_outlier_mask)),
        'rx',
        markersize=8,
        label='Positive outlier'
    )

    ax_mass_temp.plot(
        delta_T[negative_outlier_mask],
        np.zeros(np.count_nonzero(negative_outlier_mask)),
        'bx',
        markersize=8,
        label='Negative outlier'
    )

    ax_mass_temp.plot(x, y_l, 'k:', label='Linear fit')
    ax_mass_temp.plot(x, y_q, 'g--', label='Quadratic fit')
    ax_mass_temp.plot(x, y_c, 'c-.', label='Cubic fit')

    ax_mass_temp.set_xlabel('Temperature Δ (°C)')
    ax_mass_temp.set_ylabel('Mass (g)')

    # Absolute temperature axis
    ax_top = ax_mass_temp.twiny()
    ticks = ax_mass_temp.get_xticks()
    ax_top.set_xticks(ticks + REF_TEMPERATURE_C)
    ax_top.set_xlim(ax_mass_temp.get_xlim()[0] + REF_TEMPERATURE_C,
                    ax_mass_temp.get_xlim()[1] + REF_TEMPERATURE_C)
    ax_top.set_xlabel('Absolute Temperature (°C)')

    # Residuals
    ax_res = ax_mass_temp.twinx()
    ax_res.plot(x, res_q, 'm.', alpha=0.5, label='Quadratic residuals')
    ax_res.set_ylabel('Residuals (g)', color='magenta')
    ax_res.tick_params(axis='y', labelcolor='magenta')

    # Legend (explicitly include residuals)
    h1, l1 = ax_mass_temp.get_legend_handles_labels()
    h2, l2 = ax_res.get_legend_handles_labels()
    ax_mass_temp.legend(h1 + h2, l1 + l2, loc='best')

    if sensor_idx is None:
        sensor_name = 'Aggregate'
    else:
        sensor_name = f'{sensor_idx}'
    ax_mass_temp.set_title(f'S/N: {session.devices[0].serial}, '
                           f'ID: {short_uuid(session.devices[0].id)}, '
                           f'Session: {session.name},'
                           f'Sensor: {sensor_name}')

    # ------------------------------------------------------------------
    # Time series
    # ------------------------------------------------------------------
    ax_time.plot(timestamps, masses, 'b.-', label='Mass (g)')

    timestamps_np = np.asarray(timestamps)
    ax_time.plot(
        timestamps_np[positive_outlier_mask],
        np.zeros(np.count_nonzero(positive_outlier_mask)),
        'rx',
        markersize=8,
        label='Positive outlier'
    )

    ax_time.plot(
        timestamps_np[negative_outlier_mask],
        np.zeros(np.count_nonzero(negative_outlier_mask)),
        'bx',
        markersize=8,
        label='Negative outlier'
    )
    ax_t2 = ax_time.twinx()
    ax_t2.plot(timestamps, temps, 'r.-', label='Temperature (°C)')

    ax_time.set_xlabel('Time')
    ax_time.set_ylabel('Mass (g)', color='tab:blue')
    ax_t2.set_ylabel('Temperature (°C)', color='tab:red')

    # Combine legends (fixes missing temperature)
    h1, l1 = ax_time.get_legend_handles_labels()
    h2, l2 = ax_t2.get_legend_handles_labels()
    ax_time.legend(h1 + h2, l1 + l2, loc='best')

    ax_time.set_title('Mass & Temperature vs Time')

    # ------------------------------------------------------------------
    # Stats box
    # ------------------------------------------------------------------
    ax_stats.axis('off')

    def stats(res):
        rmse = np.sqrt(np.mean(res ** 2))
        s1 = np.std(res, ddof=1)
        return rmse, s1, 2 * s1, 3 * s1

    def _dc_offset_stat_str() -> str:
        if sensor_idx is None:
            return f"  Median Offset (applied): {median_offset:.2f} g\n"
        return ""

    raw_residuals = y - ref_sorted
    rmse_raw, s1r, s2r, s3r = stats(raw_residuals)
    rmse_l, s1l, s2l, s3l = stats(res_l)
    rmse_q, s1q, s2q, s3q = stats(res_q)
    rmse_c, s1c, s2c, s3c = stats(res_c)

    text =  (
        f"Reference temperature: {REF_TEMPERATURE_C} °C\n\n"

        "Datapoints:\n"
        f"  Total={total_count}\n"
        f"  Filtered={filtered_count} ({filtered_count / total_count:.4f}%)\n"
        f"  MAD={mad:.3f} g\n"
        f"  MAD Threshold={mad_threshold:.1f}\n"
        f"{_dc_offset_stat_str()}"
        f"\n"
        
        "Raw (measured vs reference):\n"
        f"  RMSE={rmse_raw:.3f} g | 1σ={s1r:.3f} | 2σ={s2r:.3f} | 3σ={s3r:.3f}\n\n"

        "Linear:\n"
        f"  Mass = {b0:.3f} + {b1:.3f}·ΔT\n"
        f"  RMSE={rmse_l:.3f} g | 1σ={s1l:.3f} | 2σ={s2l:.3f} | 3σ={s3l:.3f}\n\n"

        "Quadratic:\n"
        f"  Mass = {a0:.3f} + {a1:.3f}·ΔT + {a2:.6f}·ΔT²\n"
        f"  RMSE={rmse_q:.3f} g | 1σ={s1q:.3f} | 2σ={s2q:.3f} | 3σ={s3q:.3f}\n\n"

        "Cubic:\n"
        f"  Mass = {c0:.3f} + {c1:.3f}·ΔT + {c2:.6f}·ΔT² + {c3:.6f}·ΔT³\n"
        f"  RMSE={rmse_c:.3f} g | 1σ={s1c:.3f} | 2σ={s2c:.3f} | 3σ={s3c:.3f}"
    )

    ax_stats.text(
        0, 1, text,
        va='top', ha='left',
        fontsize=10,
        bbox=dict(boxstyle='round', facecolor='white', alpha=0.9),
    )

    fig.tight_layout()
    plt.show()

def plot_temp_cal(fuzzy_id: str):
    """
    Plots temperature correction for all sensors in the session.

    Returns a list of dicts per sensor:
      {
        "linear": (b0, b1),
        "quadratic": (a0, a1, a2),
        "cubic": (c0, c1, c2, c3)
      }
    """

    engine = get_db_engine().session
    session = engine.get(fuzzy_id)
    datapoints = engine.get_datapoints(session.id)

    if not datapoints:
        raise ServiceCmdError(f"No datapoints found for session {session.id}")

    max_sensors = len(datapoints[0].mass_sensors)

    # Passing None for the sensor index means "for the aggregate".
    for sensor_idx in (None,) + tuple(range( max_sensors)):
        _plot_temp_cal(session, datapoints, sensor_idx)


def _plot_time(datapoints: list[Row],
               mass_sensor_datapoints: list[Row],
               temp_sensor_datapoints: list[Row]):

    import numpy as np
    import matplotlib.pyplot as plt
    import datetime
    from collections import defaultdict
    from matplotlib.dates import DateFormatter, AutoDateLocator, num2date

    timestamps = np.array(
        [dp.timestamp for dp in datapoints],
        dtype="datetime64[ms]",
    )

    mass = np.array(
        [dp.mass for dp in datapoints],
        dtype=float,
    )

    temperature = np.array(
        [dp.temperature for dp in datapoints],
        dtype=float,
    )

    # -------------------------
    # Create plots
    # -------------------------

    fig, (
        (ax_mass, ax_sensor_mass),
        (ax_temp, ax_sensor_temp),
    ) = plt.subplots(
        2,
        2,
        figsize=(16, 10),
        sharex=True,
    )


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
        "green",
        "magenta",
        "black",
    ]

    sensor_mass_data = defaultdict(list)

    for row in mass_sensor_datapoints:
        sensor_mass_data[row.idx].append(
            (
                row.timestamp,
                row.mass,
            )
        )


    sensor_temp_data = defaultdict(list)

    for row in temp_sensor_datapoints:
        sensor_temp_data[row.idx].append(
            (
                row.timestamp,
                row.temperature,
            )
        )


    sensor_mass_arrays = {}
    sensor_temp_arrays = {}


    for idx, values in sorted(sensor_mass_data.items()):

        times = np.array(
            [v[0] for v in values],
            dtype="datetime64[ms]",
        )

        vals = np.array(
            [v[1] for v in values],
            dtype=float,
        )

        sensor_mass_arrays[idx] = (
            times,
            vals,
        )

        ax_sensor_mass.plot(
            times,
            vals,
            color=sensor_colors[idx % len(sensor_colors)],
            label=f"Sensor {idx}",
        )


    for idx, values in sorted(sensor_temp_data.items()):

        times = np.array(
            [v[0] for v in values],
            dtype="datetime64[ms]",
        )

        vals = np.array(
            [v[1] for v in values],
            dtype=float,
        )

        sensor_temp_arrays[idx] = (
            times,
            vals,
        )

        ax_sensor_temp.plot(
            times,
            vals,
            color=sensor_colors[idx % len(sensor_colors)],
            label=f"Sensor {idx}",
        )


    ax_sensor_mass.set_ylabel("Mass (g)")
    ax_sensor_mass.set_title("Individual Sensor Mass")
    ax_sensor_mass.legend()


    ax_sensor_temp.set_ylabel("Temperature (°C)")
    ax_sensor_temp.set_title("Individual Sensor Temperature")
    ax_sensor_temp.legend()


    # -------------------------
    # X axis formatting
    # -------------------------

    utc_formatter = DateFormatter(
        "%Y-%m-%dT%H:%M:%SZ",
        tz=datetime.timezone.utc,
    )

    locator = AutoDateLocator(
        minticks=10,
        maxticks=20,
    )

    for ax in [
        ax_mass,
        ax_sensor_mass,
        ax_temp,
        ax_sensor_temp,
    ]:
        ax.xaxis.set_major_formatter(utc_formatter)
        ax.xaxis.set_major_locator(locator)


    ax_temp.set_xlabel("Time")
    ax_sensor_temp.set_xlabel("Time")


    # -------------------------
    # Plot data registry
    # -------------------------

    plot_series = []

    def add_series(name, axis, times, values):

        plot_series.append(
            {
                "name": name,
                "axis": axis,
                "times": times,
                "values": values,
            }
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

        mean = np.mean(values)
        median = np.median(values)
        std = np.std(values)

        return (
            f"range: {elapsed}\n"
            f"min/max/med/mean: "
            f"{np.min(values):.3f}, "
            f"{np.max(values):.3f}, "
            f"{median:.3f}, "
            f"{mean:.3f}\n"
            f"1sigma/2sigma/3sigma = "
            f"{std:.3f}, "
            f"{2 * std:.3f}, "
            f"{3 * std:.3f}"
        )


    stats_text = {}

    axis_counts = defaultdict(int)

    for item in plot_series:

        key = item["name"]
        axis = item["axis"]

        # # Compact sensor statistics, larger spacing for separate plots
        # if axis in [ax_sensor_mass, ax_sensor_temp]:
        #     spacing = 0.05
        # else:
        #     spacing = 0.18
        spacing = 0.10

        y = 0.98 - axis_counts[axis] * spacing

        axis_counts[axis] += 1

        stats_text[key] = axis.text(
            0.02,
            y,
            "",
            transform=axis.transAxes,
            verticalalignment="top",
            fontsize=8,
        )


    # -------------------------
    # Helpers
    # -------------------------

    def visible_range(ax):

        x_min, x_max = ax.get_xlim()

        start = np.datetime64(
            num2date(
                x_min,
                tz=datetime.timezone.utc,
            ).replace(tzinfo=None)
        )

        end = np.datetime64(
            num2date(
                x_max,
                tz=datetime.timezone.utc,
            ).replace(tzinfo=None)
        )

        return start, end


    busy = False


    def update_view(ax):

        nonlocal busy

        if busy:
            return

        busy = True

        try:

            start, end = visible_range(ax)

            elapsed_str = get_elapsed_str(int((end-start) / np.timedelta64(1, "s")))

            axis_values = defaultdict(list)


            for item in plot_series:

                times = item["times"]
                values = item["values"]

                mask = (
                    (times >= start) &
                    (times <= end)
                )

                if not np.any(mask):
                    continue


                visible = values[mask]

                stats_text[item["name"]].set_text(
                    format_stats(visible, elapsed_str)
                )


                axis_values[item["axis"]].append(
                    visible
                )


            # -------------------------
            # Autoscale y
            # -------------------------

            for axis, values in axis_values.items():

                merged = np.concatenate(values)

                ymin = np.min(merged)
                ymax = np.max(merged)

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


    ax_mass.callbacks.connect(
        "xlim_changed",
        update_view,
    )

    update_view(ax_mass)


    fig.autofmt_xdate()
    plt.tight_layout()
    plt.show()

def plot_time(fuzzy_id: str):
    start_time = None
    end_time = None

    db_engine = get_db_engine()
    device_id = db_engine.device.get(fuzzy_id).id

    datapoints, mass_sensor_datapoints, temp_sensor_datapoints = \
        db_engine.datapoint.get_device_datapoints(device_id, start_time, end_time)

    _plot_time(datapoints, mass_sensor_datapoints, temp_sensor_datapoints)

def _extract_from_datapoints(datapoints, sensor_idx: Optional[int]):
    timestamps, masses, ref_masses, temps = [], [], [], []

    for dp in datapoints:
        if sensor_idx is None:
            if dp.ref_mass is not None:
                timestamps.append(dp.timestamp)
                masses.append(dp.mass)
                ref_masses.append(dp.ref_mass)
                temps.append(dp.temperature)
        else:
            if dp.mass_sensors[sensor_idx].ref_mass is not None:
                timestamps.append(dp.timestamp)
                masses.append(dp.mass_sensors[sensor_idx].mass)  # ADC reading
                ref_masses.append(dp.mass_sensors[sensor_idx].ref_mass)  # grams
                if len(dp.temperature_sensors) > 1:
                    temps.append(dp.temperature_sensors[sensor_idx].temperature)
                else:
                    temps.append(dp.temperature_sensors[0].temperature)

    return np.array(timestamps), np.array(masses), np.array(ref_masses), np.array(temps)

def _mad_filter(to_be_filtered, k=2.5):
    """
    Return a boolean mask of points within k*MAD of the median, where MAD means "Median Absolute
    Deviation"

    :param to_be_filtered: The data to be filtered
    :param k: The number of sigmas beyond which data will be filtered.
    """
    med = np.median(to_be_filtered)
    mad = np.median(np.abs(to_be_filtered - med))
    if mad == 0:
        return np.ones_like(to_be_filtered, dtype=bool)
    sigma = 1.4826 * mad
    return np.abs(to_be_filtered - med) <= k * sigma

def _cubic_fit(x: np.ndarray, y: np.ndarray):
    """
    Fits y = c0 + c1*x + c2*x^2 + c3*x^3
    Returns (c0, c1, c2, c3, residuals)
    """
    coeffs = np.polyfit(x, y, deg=3)
    c3, c2, c1, c0 = coeffs
    y_pred = c0 + c1*x + c2*x**2 + c3*x**3
    residuals = y - y_pred
    return c0, c1, c2, c3, residuals

def _linear_fit(x: np.ndarray, y: np.ndarray):
    """
    Fits y = b0 + b1*x
    Returns (b0, b1, residuals)
    """
    b1, b0 = np.polyfit(x, y, deg=1)
    y_pred = b0 + b1 * x
    residuals = y - y_pred
    return b0, b1, residuals

def _quadratic_fit(x: np.ndarray, y: np.ndarray) -> tuple[float, float, float, np.ndarray]:
    """
    Performs a quadratic regression: y = a0 + a1*x + a2*x^2
    Returns coefficients (a0, a1, a2) and residuals (y - y_pred).
    """
    X = np.vstack([np.ones_like(x), x, x**2]).T
    coeffs, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
    a0, a1, a2 = coeffs
    y_pred = a0 + a1*x + a2*x**2
    residuals = y - y_pred
    return a0, a1, a2, residuals

