from matplotlib.dates import DateFormatter
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import math
import numpy as np


from growbies.cli.common import Param as CommonParam
from growbies.db.engine import get_db_engine
from growbies.db.models.common import BuiltinTagName
from growbies.db.models.session import Session
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
    plot_error_plane_per_sensor_quadratic(session)

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


def plot_error_plane_per_sensor_interaction(session: Session, ref_temp: float = 22.0):
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

def plot_error_plane_per_sensor_interaction_separated(session: Session, ref_temp: float = 22.0):
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


def plot_error_plane_per_sensor_quadratic(session: Session, ref_temp: float = 22.0):
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

        # ---- Design matrix: intercept, M_ref, dT, M*dT, dT^2, M^2 ----
        A = np.c_[np.ones_like(X_ref), X_ref, dT, X_ref*dT, dT**2, X_ref**2]

        # Solve least squares
        coeff, *_ = np.linalg.lstsq(A, M_measured, rcond=None)
        c0, c1, c2, c3, c4, c5 = coeff

        # ---- Create grid for plotting surface ----
        xi = np.linspace(X_ref.min(), X_ref.max(), 20)
        yi = np.linspace(dT.min(), dT.max(), 20)
        XI, YI = np.meshgrid(xi, yi)
        ZI = c0 + c1*XI + c2*YI + c3*(XI*YI) + c4*(YI**2) + c5*(XI**2)

        # ---- Subplot for this sensor ----
        ax = fig.add_subplot(nrows, ncols, sensor_idx + 1, projection='3d')

        # Plot surface and scatter points
        ax.plot_surface(XI, YI + ref_temp, ZI, alpha=0.3, color='tab:blue', edgecolor='k')
        ax.scatter(X_ref, dT + ref_temp, M_measured, color='tab:red', s=30)

        ax.set_xlabel("Reference Mass (g)")
        ax.set_ylabel("Temperature (°C)")
        ax.set_zlabel("Measured Mass (g)")
        ax.set_title(f"Sensor {sensor_idx}")

    plt.tight_layout()
    plt.show()
