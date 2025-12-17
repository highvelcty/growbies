from matplotlib.dates import DateFormatter
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import math
import numpy as np


from growbies.cli.common import Param as CommonParam
from growbies.db.engine import get_db_engine
from growbies.db.models.common import BuiltinTagName
from growbies.db.models.session import Session
from growbies.device.common.calibration import REF_TEMPERATURE_C
from growbies.service.common import ServiceCmd, ServiceCmdError
from growbies.utils.timestamp import FMT_DT_INT


def execute(cmd: ServiceCmd):
    engine = get_db_engine().session

    fuzzy_id = cmd.kw.pop(CommonParam.FUZZY_ID)
    session = engine.get(fuzzy_id)

    # plot_mass_vs_time(session)
    # plot_ref_mass_vs_temperature(session)
    # plot_error_plane_per_sensor(session)
    # plot_error_plane_per_sensor_interaction_separated(session)
    # plot_error_plane_per_sensor_quadratic(session)
    # plot_error_heatmap_mass_per_sensor(session)
    # plot_residual_vs_corrected_mass(session)
    # plot_mass_vs_temp(session)
    # plot_mass_cal(session)
    plot_temperature_correction(session)

def plot_mass_vs_time(session: Session):
    engine = get_db_engine().session
    datapoints = engine.get_datapoints(session.id)

    if not datapoints:
        raise ServiceCmdError(f"No datapoints found for session {session.id}")

    # ---- Extract main mass ----
    timestamps = [dp.timestamp for dp in datapoints]
    mass_values = [dp.mass for dp in datapoints]

    # ---- Extract per-sensor mass ----
    max_sensors = len(datapoints[0].mass_sensors)

    # sensor_traces[i] = list of mass values for sensor i
    sensor_traces = [[] for _ in range(max_sensors)]

    for dp in datapoints:
        # enforce ordering, in case the DB order isn't stable
        sensors_sorted = sorted(dp.mass_sensors, key=lambda s: s.idx)

        for i in range(max_sensors):
            if i < len(sensors_sorted):
                sensor_traces[i].append(sensors_sorted[i].mass)
            else:
                # no value — keep timeline consistent
                sensor_traces[i].append(None)

    # ---- Temperature ----
    temperature_values = [dp.temperature for dp in datapoints]

    # ---- Plot ----
    fig, ax_mass = plt.subplots()

    # Left y-axis: Mass
    ax_mass.plot(timestamps, mass_values, label="Aggregate Mass", linewidth=2)
    # per-sensor lines
    for i in range(max_sensors):
        ax_mass.plot(timestamps, sensor_traces[i], label=f"Sensor {i} mass")

    ax_mass.set_ylabel("Mass (g)")
    ax_mass.set_xlabel("Time")
    ax_mass.legend(loc="upper left")
    ax_mass.set_title(f"Mass & Temperature session {session.name}")

    # Right y-axis: Temperature
    ax_temp = ax_mass.twinx()
    ax_temp.plot(timestamps, temperature_values, label="Temperature", color="tab:red", linewidth=2)
    ax_temp.set_ylabel("Temperature (°C)")
    ax_temp.legend(loc="upper right")

    # Format x-axis with ISO UTC
    ax_mass.xaxis.set_major_formatter(DateFormatter(FMT_DT_INT))
    fig.autofmt_xdate()
    plt.tight_layout()
    plt.show()

def plot_mass_vs_time(session: Session):
    engine = get_db_engine().session
    datapoints = engine.get_datapoints(session.id)

    if not datapoints:
        raise ServiceCmdError(f"No datapoints found for session {session.id}")

    # ---- Extract main mass ----
    timestamps = [dp.timestamp for dp in datapoints]
    mass_values = [dp.mass for dp in datapoints]

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
    ax_mass.plot(timestamps, mass_values, label="Aggregate Mass", linewidth=2)
    ax_mass.scatter(timestamps, mass_values, alpha=0.7, marker='.')

    # Per-sensor lines + dots
    for i in range(max_sensors):
        ax_mass.plot(timestamps, sensor_traces[i], label=f"Sensor {i} mass")
        ax_mass.scatter(timestamps, sensor_traces[i], alpha=0.7, marker = '.')

    ax_mass.set_ylabel("Mass (g)")
    ax_mass.set_xlabel("Time")
    ax_mass.legend(loc="upper left")
    ax_mass.set_title(f"Mass & Temperature session {session.name}")

    # Right y-axis: Temperature
    ax_temp = ax_mass.twinx()
    ax_temp.plot(timestamps, temperature_values, label="Temperature", color="tab:red", linewidth=2)
    ax_temp.scatter(timestamps, temperature_values, color="tab:red", alpha=0.7, marker='.')
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

def plot_error_plane_per_sensor(session: Session):
    engine = get_db_engine().session
    datapoints = engine.get_datapoints(session.id)

    if not datapoints:
        raise ServiceCmdError(f"No datapoints found for session {session.id}")

    max_sensors = len(datapoints[0].mass_sensors)

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    # Use a colormap for different sensors
    colors = plt.cm.tab10(np.linspace(0, 1, max_sensors))

    for sensor_idx in range(max_sensors):
        temp_list = []
        ref_list = []
        error_list = []

        for dp in datapoints:
            if sensor_idx < len(dp.mass_sensors):
                sensor = dp.mass_sensors[sensor_idx]
                if sensor.ref_mass is not None:
                    temp_list.append(dp.temperature)
                    ref_list.append(sensor.ref_mass)
                    error_list.append(sensor.mass - sensor.ref_mass)

        if not temp_list:
            continue  # Skip sensors with no reference mass

        X = np.array(temp_list)
        Y = np.array(ref_list)
        Z = np.array(error_list)

        # ---- Fit plane: Z = a*X + b*Y + c ----
        A = np.c_[X, Y, np.ones_like(X)]
        coeff, *_ = np.linalg.lstsq(A, Z, rcond=None)
        a, b, c = coeff

        # ---- Create grid for plotting plane ----
        xi = np.linspace(X.min(), X.max(), 20)
        yi = np.linspace(Y.min(), Y.max(), 20)
        XI, YI = np.meshgrid(xi, yi)
        ZI = a * XI + b * YI + c

        # ---- Plot plane ----
        ax.plot_surface(XI, YI, ZI, alpha=0.3, color=colors[sensor_idx], edgecolor='k')

        # ---- Plot scatter points ----
        ax.scatter(X, Y, Z, color=colors[sensor_idx], label=f"Sensor {sensor_idx}", s=30)

    ax.set_xlabel("Temperature (°C)")
    ax.set_ylabel("Reference Mass (g)")
    ax.set_zlabel("Error (Measured - Reference, g)")
    ax.set_title(f"Error Planes per Sensor for Session {session.name}")
    ax.legend()
    plt.tight_layout()
    plt.show()


def plot_error_plane_per_sensor_interaction(session: Session, ref_temp: float = REF_TEMPERATURE_C):
    engine = get_db_engine().session
    datapoints = engine.get_datapoints(session.id)

    if not datapoints:
        raise ServiceCmdError(f"No datapoints found for session {session.id}")

    max_sensors = len(datapoints[0].mass_sensors)

    for sensor_idx in range(max_sensors):
        temp_list = []
        ref_list = []
        mass_list = []

        for dp in datapoints:
            if sensor_idx < len(dp.mass_sensors):
                sensor = dp.mass_sensors[sensor_idx]
                if sensor.ref_mass is not None:
                    if sensor_idx == 1:
                        print(sensor.mass)
                    temp_list.append(dp.temperature)
                    ref_list.append(sensor.ref_mass)
                    mass_list.append(sensor.mass)

        if not temp_list:
            continue  # Skip sensors with no reference mass

        X_ref = np.array(ref_list)
        dT = np.array(temp_list) - ref_temp   # reference temperature
        M_measured = np.array(mass_list)

        # ---- Design matrix: intercept, ref_mass, dT, ref_mass*dT ----
        A = np.c_[np.ones_like(X_ref), X_ref, dT, X_ref * dT]

        # Solve least squares
        coeff, *_ = np.linalg.lstsq(A, M_measured, rcond=None)
        c0, c1, c2, c3 = coeff

        # ---- Create grid for plotting plane ----
        xi = np.linspace(X_ref.min(), X_ref.max(), 20)
        yi = np.linspace(dT.min(), dT.max(), 20)
        XI, YI = np.meshgrid(xi, yi)
        ZI = c0 + c1*XI + c2*YI + c3*(XI*YI)

        # ---- Create figure for this sensor ----
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')

        # Plot plane
        ax.plot_surface(XI, YI + ref_temp, ZI, alpha=0.3, color='tab:blue', edgecolor='k')

        # Plot scatter points
        ax.scatter(X_ref, dT + ref_temp, M_measured, color='tab:red', label=f"Sensor {sensor_idx}", s=30)

        ax.set_xlabel("Reference Mass (g)")
        ax.set_ylabel("Temperature (°C)")
        ax.set_zlabel("Measured Mass (g)")
        ax.set_title(f"Sensor {sensor_idx} Mass Plane - Session {session.name}")
        ax.legend()
        plt.tight_layout()
        plt.show()

def plot_error_plane_per_sensor_interaction_separated(session: Session,
                                                      ref_temp: float = REF_TEMPERATURE_C):
    engine = get_db_engine().session
    datapoints = engine.get_datapoints(session.id)

    if not datapoints:
        raise ServiceCmdError(f"No datapoints found for session {session.id}")

    max_sensors = len(datapoints[0].mass_sensors)

    # Determine subplot grid size
    ncols = 2
    nrows = math.ceil(max_sensors / ncols)

    fig = plt.figure(figsize=(6 * ncols, 5 * nrows))

    for sensor_idx in range(max_sensors):
        temp_list = []
        ref_list = []
        mass_list = []

        for dp in datapoints:
            if sensor_idx < len(dp.mass_sensors):
                sensor = dp.mass_sensors[sensor_idx]
                if sensor.ref_mass is not None:
                    temp_list.append(dp.temperature)
                    ref_list.append(sensor.ref_mass)
                    mass_list.append(sensor.mass)

        if not temp_list:
            continue  # Skip sensors with no reference mass

        X_ref = np.array(ref_list)
        dT = np.array(temp_list) - ref_temp
        M_measured = np.array(mass_list)

        # Design matrix for interaction model
        A = np.c_[np.ones_like(X_ref), X_ref, dT, X_ref * dT]
        coeff, *_ = np.linalg.lstsq(A, M_measured, rcond=None)
        c0, c1, c2, c3 = coeff

        # Grid for plane
        xi = np.linspace(X_ref.min(), X_ref.max(), 20)
        yi = np.linspace(dT.min(), dT.max(), 20)
        XI, YI = np.meshgrid(xi, yi)
        ZI = c0 + c1*XI + c2*YI + c3*(XI*YI)

        # Add subplot for this sensor
        ax = fig.add_subplot(nrows, ncols, sensor_idx + 1, projection='3d')

        # Plot plane and scatter
        ax.plot_surface(XI, YI + ref_temp, ZI, alpha=0.3, color='tab:blue', edgecolor='k')
        ax.scatter(X_ref, dT + ref_temp, M_measured, color='tab:red', s=30)

        ax.set_xlabel("Reference Mass (g)")
        ax.set_ylabel("Temperature (°C)")
        ax.set_zlabel("Measured Mass (g)")
        ax.set_title(f"Sensor {sensor_idx}")

    plt.tight_layout()
    plt.show()


# def plot_error_plane_per_sensor_quadratic(session: Session, ref_temp: float = REF_TEMPERATURE_C):
#     engine = get_db_engine().session
#     datapoints = engine.get_datapoints(session.id)
#
#     if not datapoints:
#         raise ServiceCmdError(f"No datapoints found for session {session.id}")
#
#     max_sensors = len(datapoints[0].mass_sensors)
#
#     # Determine subplot grid size
#     ncols = 2
#     nrows = math.ceil(max_sensors / ncols)
#     fig = plt.figure(figsize=(6 * ncols, 5 * nrows))
#
#     for sensor_idx in range(max_sensors):
#         temp_list = []
#         ref_list = []
#         mass_list = []
#
#         for dp in datapoints:
#             if sensor_idx < len(dp.mass_sensors):
#                 sensor = dp.mass_sensors[sensor_idx]
#                 if sensor.ref_mass is not None:
#                     temp_list.append(dp.temperature)
#                     ref_list.append(sensor.ref_mass)
#                     mass_list.append(sensor.mass)
#
#         if not temp_list:
#             continue  # Skip sensors with no reference mass
#
#         X_ref = np.array(ref_list)
#         dT = np.array(temp_list) - ref_temp
#         M_measured = np.array(mass_list)
#
#         # ---- Design matrix: intercept, M_ref, dT, M*dT, dT^2, M^2 ----
#         A = np.c_[np.ones_like(X_ref), X_ref, dT, X_ref*dT, dT**2, X_ref**2]
#
#         # Solve least squares
#         coeff, *_ = np.linalg.lstsq(A, M_measured, rcond=None)
#         c0, c1, c2, c3, c4, c5 = coeff
#
#         # ---- Create grid for plotting surface ----
#         xi = np.linspace(X_ref.min(), X_ref.max(), 20)
#         yi = np.linspace(dT.min(), dT.max(), 20)
#         XI, YI = np.meshgrid(xi, yi)
#         ZI = c0 + c1*XI + c2*YI + c3*(XI*YI) + c4*(YI**2) + c5*(XI**2)
#
#         # ---- Subplot for this sensor ----
#         ax = fig.add_subplot(nrows, ncols, sensor_idx + 1, projection='3d')
#
#         # Plot surface and scatter points
#         ax.plot_surface(XI, YI + ref_temp, ZI, alpha=0.3, color='tab:blue', edgecolor='k')
#         ax.scatter(X_ref, dT + ref_temp, M_measured, color='tab:red', s=30)
#
#         ax.set_xlabel("Reference Mass (g)")
#         ax.set_ylabel("Temperature (°C)")
#         ax.set_zlabel("Measured Mass (g)")
#         ax.set_title(f"Sensor {sensor_idx}")
#
#     plt.tight_layout()
#     plt.show()

# def plot_error_plane_per_sensor_quadratic(session: Session, ref_temp: float = REF_TEMPERATURE_C):
#     engine = get_db_engine().session
#     datapoints = engine.get_datapoints(session.id)
#
#     if not datapoints:
#         raise ServiceCmdError(f"No datapoints found for session {session.id}")
#
#     max_sensors = len(datapoints[0].mass_sensors)
#
#     # Determine subplot grid size
#     ncols = 2
#     nrows = math.ceil(max_sensors / ncols)
#     fig = plt.figure(figsize=(6 * ncols, 5 * nrows))
#
#     for sensor_idx in range(max_sensors):
#         temp_list = []
#         ref_list = []
#         mass_list = []
#
#         for dp in datapoints:
#             if sensor_idx < len(dp.mass_sensors):
#                 sensor = dp.mass_sensors[sensor_idx]
#                 if sensor.ref_mass is not None:
#                     temp_list.append(dp.temperature)
#                     ref_list.append(sensor.ref_mass)
#                     mass_list.append(sensor.mass)
#
#         if not temp_list:
#             continue  # Skip sensors with no reference mass
#
#         X_ref = np.array(ref_list)
#         dT = np.array(temp_list) - ref_temp
#         M_measured = np.array(mass_list)
#
#         # ---- Design matrix: intercept, M_ref, dT, M*dT, dT^2, M^2 ----
#         A = np.c_[
#             np.ones_like(X_ref),
#             X_ref,
#             dT,
#             X_ref * dT,
#             dT**2,
#             X_ref**2,
#         ]
#
#         # Solve least squares
#         coeff, *_ = np.linalg.lstsq(A, M_measured, rcond=None)
#         c0, c1, c2, c3, c4, c5 = coeff
#
#         # ---- Create grid for plotting surface ----
#         xi = np.linspace(X_ref.min(), X_ref.max(), 20)
#         yi = np.linspace(dT.min(), dT.max(), 20)
#         XI, YI = np.meshgrid(xi, yi)
#         ZI = (
#             c0
#             + c1 * XI
#             + c2 * YI
#             + c3 * (XI * YI)
#             + c4 * (YI**2)
#             + c5 * (XI**2)
#         )
#
#         # ---- Subplot for this sensor ----
#         ax = fig.add_subplot(nrows, ncols, sensor_idx + 1, projection="3d")
#
#         ax.plot_surface(
#             XI,
#             YI + ref_temp,
#             ZI,
#             alpha=0.3,
#             edgecolor="k",
#         )
#         ax.scatter(
#             X_ref,
#             dT + ref_temp,
#             M_measured,
#             s=30,
#         )
#
#         ax.set_xlabel("Reference Mass (g)")
#         ax.set_ylabel("Temperature (°C)")
#         ax.set_zlabel("Measured Mass (g)")
#         ax.set_title(f"Sensor {sensor_idx}")
#
#         # ---- Coefficient text block ----
#         coeff_text = (
#             "Model coefficients:\n"
#             f"c0 = {c0:.4e}\n"
#             f"c1 = {c1:.4e}\n"
#             f"c2 = {c2:.4e}\n"
#             f"c3 = {c3:.4e}\n"
#             f"c4 = {c4:.4e}\n"
#             f"c5 = {c5:.4e}"
#         )
#
#         ax.text2D(
#             0.02,
#             0.98,
#             coeff_text,
#             transform=ax.transAxes,
#             fontsize=9,
#             verticalalignment="top",
#             bbox=dict(boxstyle="round", alpha=0.8),
#         )
#
#     plt.tight_layout()
#     plt.show()

def plot_error_plane_per_sensor_quadratic(session: "Session", ref_temp: float = REF_TEMPERATURE_C):
    """
    Plot 3D reference mass vs raw ADC & temperature for each sensor in a session,
    showing both raw RMSE and corrected RMSE per sensor.
    """
    engine = get_db_engine().session
    datapoints = engine.get_datapoints(session.id)

    if not datapoints:
        raise ServiceCmdError(f"No datapoints found for session {session.id}")

    max_sensors = len(datapoints[0].mass_sensors)
    ncols = 2
    nrows = math.ceil(max_sensors / ncols)
    fig = plt.figure(figsize=(6 * ncols, 5 * nrows))

    # ---- Figure-level model title ----
    model_str = "M_ref = c0 + c1·r + c2·dT + c3·(r·dT) + c4·(dT²) + c5·(r²)"
    fig.suptitle(model_str, fontsize=12, y=0.98)

    for sensor_idx in range(max_sensors):
        temp_list = []
        ref_list = []
        r_list = []

        for dp in datapoints:
            if sensor_idx < len(dp.mass_sensors):
                sensor = dp.mass_sensors[sensor_idx]
                if sensor.ref_mass is not None:
                    temp_list.append(dp.temperature)
                    ref_list.append(sensor.ref_mass)
                    r_list.append(sensor.mass)  # raw ADC reading

        if not temp_list:
            continue  # Skip sensors with no reference mass

        r = np.array(r_list)
        dT = np.array(temp_list) - ref_temp
        M_ref = np.array(ref_list)

        # ---- Raw RMSE (before correction) ----
        raw_rmse = np.sqrt(np.mean((r - M_ref)**2))

        # ---- Design matrix for polynomial correction ----
        A = np.c_[
            np.ones_like(r),
            r,
            dT,
            r * dT,
            dT**2,
            r**2,
        ]

        # ---- Solve least squares for corrected mass ----
        coeff, *_ = np.linalg.lstsq(A, M_ref, rcond=None)
        c0, c1, c2, c3, c4, c5 = coeff

        # ---- Corrected RMSE (residual after correction) ----
        M_fit = A @ coeff
        residuals = M_fit - M_ref
        corrected_rmse = np.sqrt(np.mean(residuals**2))

        # ---- Surface grid ----
        r_grid = np.linspace(r.min(), r.max(), 20)
        dT_grid = np.linspace(dT.min(), dT.max(), 20)
        R, DT = np.meshgrid(r_grid, dT_grid)
        ZI = c0 + c1*R + c2*DT + c3*(R*DT) + c4*(DT**2) + c5*(R**2)

        # ---- 3D plot ----
        ax = fig.add_subplot(nrows, ncols, sensor_idx + 1, projection="3d")
        ax.plot_surface(R, DT + ref_temp, ZI, alpha=0.3, edgecolor="k")
        ax.scatter(r, dT + ref_temp, M_ref, s=30)

        ax.set_xlabel("Raw ADC r")
        ax.set_ylabel("Temperature (°C)")
        ax.set_zlabel("Reference Mass (g)")
        ax.set_title(f"Sensor {sensor_idx}")

        # ---- Coefficients + RMSE block ----
        coeff_text = (
            "Coefficients:\n"
            f"c0 = {c0:.6f}\n"
            f"c1 = {c1:.6f}\n"
            f"c2 = {c2:.6f}\n"
            f"c3 = {c3:.6f}\n"
            f"c4 = {c4:.6f}\n"
            f"c5 = {c5:.6f}\n\n"
            f"Raw RMSE = {raw_rmse:.3f} g\n"
            f"Corrected RMSE = {corrected_rmse:.3f} g"
        )

        ax.text2D(
            0.02,
            0.98,
            coeff_text,
            transform=ax.transAxes,
            fontsize=9,
            verticalalignment="top",
            bbox=dict(boxstyle="round", alpha=0.8),
        )

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.show()

def plot_error_heatmap_mass_per_sensor(session: "Session", ref_temp: float = REF_TEMPERATURE_C,
                                       grid_size: int = 100):
    """
    Plot a smooth 2D heatmap of residuals vs corrected mass & temperature per sensor.
    Corrected mass is computed from the polynomial model.
    """
    engine = get_db_engine().session
    datapoints = engine.get_datapoints(session.id)

    if not datapoints:
        raise ServiceCmdError(f"No datapoints found for session {session.id}")

    max_sensors = len(datapoints[0].mass_sensors)
    ncols = 2
    nrows = (max_sensors + 1) // ncols
    fig, axes = plt.subplots(nrows, ncols, figsize=(6 * ncols, 5 * nrows), squeeze=False)
    fig.suptitle("Residuals Heatmap per Sensor (Corrected Mass)", fontsize=14, y=0.98)

    for sensor_idx in range(max_sensors):
        temp_list = []
        ref_list = []
        r_list = []

        for dp in datapoints:
            if sensor_idx < len(dp.mass_sensors):
                sensor = dp.mass_sensors[sensor_idx]
                if sensor.ref_mass is not None:
                    temp_list.append(dp.temperature)
                    ref_list.append(sensor.ref_mass)
                    r_list.append(sensor.mass)

        if not temp_list:
            continue

        r = np.array(r_list)
        dT = np.array(temp_list) - ref_temp
        M_ref = np.array(ref_list)

        # Polynomial fit
        A = np.c_[
            np.ones_like(r),
            r,
            dT,
            r * dT,
            dT**2,
            r**2,
        ]
        coeff, *_ = np.linalg.lstsq(A, M_ref, rcond=None)
        M_fit = A @ coeff
        residuals = M_fit - M_ref

        # Grid for smooth heatmap
        M_lin = np.linspace(M_fit.min(), M_fit.max(), grid_size)
        dT_lin = np.linspace(dT.min(), dT.max(), grid_size)
        M_grid, DT_grid = np.meshgrid(M_lin, dT_lin)

        # Inverse-distance weighting interpolation
        Z_grid = np.zeros_like(M_grid)
        for i in range(grid_size):
            for j in range(grid_size):
                distances = np.sqrt((M_fit - M_grid[i, j])**2 + (dT - DT_grid[i, j])**2)
                distances[distances == 0] = 1e-10
                weights = 1 / distances
                Z_grid[i, j] = np.sum(weights * residuals) / np.sum(weights)

        # Plot heatmap
        ax = axes[sensor_idx // ncols, sensor_idx % ncols]
        c = ax.pcolormesh(M_grid, DT_grid + ref_temp, Z_grid, shading='auto', cmap='RdBu_r')
        ax.set_xlabel("Corrected Mass (g)")
        ax.set_ylabel("Temperature (°C)")
        ax.set_title(f"Sensor {sensor_idx}")
        fig.colorbar(c, ax=ax, label="Residual (g)")

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.show()


def plot_relative_error_vs_corrected_mass(session: "Session", ref_temp: float = REF_TEMPERATURE_C):
    """
    Plot relative error (%) vs corrected mass for each sensor in a session.
    Corrected mass is computed from the polynomial model:
    M_corrected = c0 + c1*M + c2*dT + c3*(M*dT) + c4*(dT^2) + c5*(M^2)
    Relative error = (M_corrected - ref_mass) / ref_mass * 100
    """
    engine = get_db_engine().session
    datapoints = engine.get_datapoints(session.id)

    if not datapoints:
        raise ServiceCmdError(f"No datapoints found for session {session.id}")

    max_sensors = len(datapoints[0].mass_sensors)
    ncols = 2
    nrows = (max_sensors + 1) // ncols
    fig, axes = plt.subplots(nrows, ncols, figsize=(6 * ncols, 5 * nrows), squeeze=False)
    fig.suptitle("Relative Error vs Corrected Mass per Sensor", fontsize=14, y=0.98)

    for sensor_idx in range(max_sensors):
        temp_list = []
        ref_list = []
        raw_mass_list = []

        for dp in datapoints:
            if sensor_idx < len(dp.mass_sensors):
                sensor = dp.mass_sensors[sensor_idx]
                if sensor.ref_mass is not None:
                    temp_list.append(dp.temperature)
                    ref_list.append(sensor.ref_mass)
                    raw_mass_list.append(sensor.mass)

        if not temp_list:
            continue

        r = np.array(raw_mass_list)
        dT = np.array(temp_list) - ref_temp
        M_ref = np.array(ref_list)

        # Polynomial fit for correction
        A = np.c_[
            np.ones_like(r),
            r,
            dT,
            r * dT,
            dT**2,
            r**2,
        ]
        coeff, *_ = np.linalg.lstsq(A, M_ref, rcond=None)
        M_corrected = A @ coeff

        # Relative error
        rel_error = (M_corrected - M_ref) / M_ref * 100

        # Plot
        ax = axes[sensor_idx // ncols, sensor_idx % ncols]
        ax.scatter(M_corrected, rel_error, alpha=0.7)
        ax.axhline(0, color='black', linestyle='--', linewidth=1)
        ax.set_xlabel("Corrected Mass (g)")
        ax.set_ylabel("Relative Error (%)")
        ax.set_title(f"Sensor {sensor_idx}")
        ax.grid(True)

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.show()

import numpy as np
import matplotlib.pyplot as plt

def plot_residual_vs_corrected_mass(session: "Session", ref_temp: float = REF_TEMPERATURE_C):
    """
    Plot residuals (corrected mass - reference mass) in grams vs corrected mass for each sensor.
    Corrected mass is computed from the polynomial model:
    M_corrected = c0 + c1*M + c2*dT + c3*(M*dT) + c4*(dT^2) + c5*(M^2)
    """
    engine = get_db_engine().session
    datapoints = engine.get_datapoints(session.id)

    if not datapoints:
        raise ServiceCmdError(f"No datapoints found for session {session.id}")

    max_sensors = len(datapoints[0].mass_sensors)
    ncols = 2
    nrows = (max_sensors + 1) // ncols
    fig, axes = plt.subplots(nrows, ncols, figsize=(6 * ncols, 5 * nrows), squeeze=False)
    fig.suptitle("Residual vs Corrected Mass per Sensor", fontsize=14, y=0.98)

    for sensor_idx in range(max_sensors):
        temp_list = []
        ref_list = []
        raw_mass_list = []

        for dp in datapoints:
            if sensor_idx < len(dp.mass_sensors):
                sensor = dp.mass_sensors[sensor_idx]
                if sensor.ref_mass is not None:
                    temp_list.append(dp.temperature)
                    ref_list.append(sensor.ref_mass)
                    raw_mass_list.append(sensor.mass)

        if not temp_list:
            continue

        r = np.array(raw_mass_list)
        dT = np.array(temp_list) - ref_temp
        M_ref = np.array(ref_list)

        # Polynomial fit for correction
        A = np.c_[
            np.ones_like(r),
            r,
            dT,
            r * dT,
            dT**2,
            r**2,
        ]
        coeff, *_ = np.linalg.lstsq(A, M_ref, rcond=None)
        M_corrected = A @ coeff

        # Residual in grams
        residual = M_corrected - M_ref

        # Plot
        ax = axes[sensor_idx // ncols, sensor_idx % ncols]
        ax.scatter(M_corrected, residual, alpha=0.7)
        ax.axhline(0, color='black', linestyle='--', linewidth=1)
        ax.set_xlabel("Corrected Mass (g)")
        ax.set_ylabel("Residual (g)")
        ax.set_title(f"Sensor {sensor_idx}")
        ax.grid(True)

    plt.tight_layout(rect=[0, 0, 1, 0.95])
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


def plot_mass_cal(session: "Session"):
    engine = get_db_engine().session
    datapoints = engine.get_datapoints(session.id)

    if not datapoints:
        raise ServiceCmdError(f"No datapoints found for session {session.id}")

    max_sensors = len(datapoints[0].mass_sensors)

    for sensor_idx in range(max_sensors):
        timestamps = []
        adc = []
        ref_mass = []
        sensor_temp = []

        for dp in datapoints:
            if dp.mass_sensors[sensor_idx].ref_mass is not None:
                timestamps.append(dp.timestamp)
                adc.append(dp.mass_sensors[sensor_idx].mass)        # ADC reading
                ref_mass.append(dp.mass_sensors[sensor_idx].ref_mass)  # grams
                sensor_temp.append(dp.temperature_sensors[sensor_idx].temperature)

        timestamps = np.array(timestamps)
        adc = np.array(adc, dtype=float)
        ref_mass = np.array(ref_mass, dtype=float)
        sensor_temp = np.array(sensor_temp, dtype=float)

        # --- Sort by reference mass (for plotting continuity only) ---
        sort_idx = np.argsort(ref_mass)
        ref_mass_sorted = ref_mass[sort_idx]
        adc_sorted = adc[sort_idx]
        sensor_temp_sorted = sensor_temp[sort_idx]

        # ============================================================
        # CALIBRATION MODEL
        #
        # We fit:
        #   ref_mass (g) = a0 + a1 * ADC + a2 * ADC^2
        #
        # This matches firmware usage EXACTLY.
        # ============================================================
        X = np.vstack([
            np.ones_like(adc_sorted),
            adc_sorted,
            adc_sorted ** 2
        ]).T

        coeffs, residuals, rank, s = np.linalg.lstsq(X, ref_mass_sorted, rcond=None)
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
        ax1.plot(timestamps, adc, 'b.-', label='ADC Reading')
        ax1.set_xlabel('Timestamp')
        ax1.set_ylabel('ADC', color='tab:blue')
        ax1.tick_params(axis='y', labelcolor='tab:blue')

        ax2 = ax1.twinx()
        ax2.plot(timestamps, sensor_temp, 'r.-', label='Temp (°C)')
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

def plot_temperature_correction(session: "Session"):
    """
    Plots temperature correction for all sensors in the session.
    For each sensor, produces:
      1. Mass & Temperature vs Time
      2. Mass vs Temperature Δ (T - Tref) with quadratic regression fit
         Bottom x-axis: ΔT for regression
         Top x-axis: absolute temperature
    Returns a list of coefficient tuples [(a0, a1, a2), ...] for each sensor.
    """
    engine = get_db_engine().session
    datapoints = engine.get_datapoints(session.id)

    if not datapoints:
        raise ServiceCmdError(f"No datapoints found for session {session.id}")

    max_sensors = len(datapoints[0].mass_sensors)
    all_coeffs = []

    for sensor_idx in range(max_sensors):
        timestamps = []
        masses = []
        ref_masses = []
        temps = []

        for dp in datapoints:
            mass = dp.mass_sensors[sensor_idx].mass
            ref_mass = dp.mass_sensors[sensor_idx].ref_mass
            if ref_mass is not None and mass < 40:
                timestamps.append(dp.timestamp)
                masses.append(mass)
                ref_masses.append(ref_mass)
                temps.append(dp.temperature_sensors[sensor_idx].temperature)

        timestamps = np.array(timestamps)
        masses = np.array(masses)
        ref_masses = np.array(ref_masses)
        temps = np.array(temps)

        # --- Subplot 1: Mass & Temperature vs Time ---
        fig, (ax_time, ax_mass_temp) = plt.subplots(2, 1, figsize=(12, 10))

        ax1 = ax_time
        ax1.plot(timestamps, masses, 'b.-', label='Mass (g)')
        ax1.set_xlabel('Time')
        ax1.set_ylabel('Mass (g)', color='tab:blue')
        ax1.tick_params(axis='y', labelcolor='tab:blue')

        ax2 = ax1.twinx()
        ax2.plot(timestamps, temps, 'r.-', label='Temperature (°C)')
        ax2.set_ylabel('Temperature (°C)', color='tab:red')
        ax2.tick_params(axis='y', labelcolor='tab:red')

        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='best')
        ax1.set_title(f'Sensor {sensor_idx}: Mass & Temperature vs Time')

        # --- Subplot 2: Mass vs Temperature Δ ---
        delta_T = temps - REF_TEMPERATURE_C
        x_sorted_idx = np.argsort(delta_T)
        delta_T_sorted = delta_T[x_sorted_idx]
        mass_sorted = masses[x_sorted_idx]
        ref_masses_sorted =ref_masses[x_sorted_idx]
        abs_temp_sorted = temps[x_sorted_idx]

        # Quadratic fit in ΔT
        a0, a1, a2, residuals = _quadratic_fit(delta_T_sorted, mass_sorted)
        rmse = np.sqrt(np.mean(residuals**2))
        sigma1 = np.std(residuals, ddof=1)
        sigma2 = 2 * sigma1
        sigma3 = 3 * sigma1
        mass_pred = a0 + a1*delta_T_sorted + a2*delta_T_sorted**2

        ax3 = ax_mass_temp
        ax3.plot(delta_T_sorted, mass_sorted, 'b.-', label='Mass (g)')
        ax3.plot(delta_T_sorted, mass_pred, 'g--', label='Quadratic Fit')
        ax3.set_xlabel('Temperature Δ (°C)')
        ax3.set_ylabel('Mass (g)', color='tab:blue')
        ax3.tick_params(axis='y', labelcolor='tab:blue')

        # --- Twin-x for absolute temperature ---
        ax_top = ax3.twiny()
         # Align top axis ticks with bottom axis by using a fixed transform
        bottom_ticks = ax3.get_xticks()
        ax_top.set_xticks(bottom_ticks + REF_TEMPERATURE_C)
        ax_top.set_xlim(ax3.get_xlim()[0] + REF_TEMPERATURE_C,
                        ax3.get_xlim()[1] + REF_TEMPERATURE_C)
        ax_top.set_xlabel('Absolute Temperature (°C)')

        # Residuals on secondary y-axis
        ax4 = ax3.twinx()
        ax4.plot(delta_T_sorted, residuals, 'm.-', label='Residuals (g)', alpha=.5)
        for s, style in zip([sigma1, sigma2, sigma3], ['--', ':', '-.']):
            ax4.axhline(s, color='gray', linestyle=style, linewidth=0.8)
            ax4.axhline(-s, color='gray', linestyle=style, linewidth=0.8)
        ax4.set_ylabel('Residuals (g)', color='magenta')
        ax4.tick_params(axis='y', labelcolor='magenta')

        lines3, labels3 = ax3.get_legend_handles_labels()
        lines4, labels4 = ax4.get_legend_handles_labels()
        ax3.legend(lines3 + lines4, labels3 + labels4, loc='best')

        # Raw statistics - measured vs reference
        raw_residuals = mass_sorted - ref_masses_sorted
        rmse_raw = np.sqrt(np.mean(raw_residuals ** 2))
        sigma1_raw = np.std(raw_residuals, ddof=1)
        sigma2_raw = 2 * sigma1_raw
        sigma3_raw = 3 * sigma1_raw

        coeff_text = (
            f"Mass_corrected = {a0:.3f} + {a1:.3f}*ΔT + {a2:.6f}*ΔT^2\n"
            f'Reference Temperature (°C) = {REF_TEMPERATURE_C}\n'
            f"RMSE = {rmse:.3f} g, 1σ = {sigma1:.3f} g, 2σ = {sigma2:.3f} g, 3σ = {sigma3:.3f} g\n"
            f"RMSE raw = {rmse_raw:.3f} g, 1σ = {sigma1_raw:.3f} g, 2σ = {sigma2_raw:.3f} g, "
            f"3σ = {sigma3_raw:.3f} g\n"
        )
        ax3.text(0.02, 0.95, coeff_text, transform=ax3.transAxes,
                 fontsize=10, verticalalignment='top',
                 bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

        ax3.set_title(f'Sensor {sensor_idx}: Mass vs Temperature Δ')

        fig.tight_layout()
        plt.show()

        all_coeffs.append((a0, a1, a2))

    return all_coeffs


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