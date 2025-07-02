from datetime import datetime
from pathlib import Path
from typing import Optional

from growbies.utils import timestamp
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.axis import Axis
import tkinter as tk
import matplotlib

matplotlib.use('TkAgg')

def normalize_list(data):
    min_val = min(data)
    max_val = max(data)
    normalized_data = [(x - min_val) / (max_val - min_val) for x in data]
    return normalized_data

def _extract_x_data_and_y_datas(path: Path) -> \
        tuple[list[datetime],
              list[list[int]],
              list[datetime],
              list[int]]:
    labels = None
    x_data: list[datetime] = list()
    y_datas: list[list[float]] = list()
    ref_x_data: list[datetime] = list()
    ref_y_data: list[int] = list()
    with open(path, 'r') as inf:
        for line in inf.readlines():
            line = line.strip()
            if labels is None:
                labels = line.split(',')
                y_datas.extend(([] for _ in range(len(labels) - 2)))
            else:
                data = line.split(',')
                ref_data = None
                dt = timestamp.get_utc_dt(data[0])
                x_data.append(dt)
                data = data[1:]
                if len(data) >= (len(labels) - 1):
                    ref_data = int(data[-1])
                    data = data[:-1]

                for channel, channel_data in enumerate(data):
                    channel_data = channel_data.strip()
                    y_datas[channel].append(float(channel_data))

                if ref_data is not None:
                    ref_x_data.append(dt)
                    ref_y_data.append(ref_data)

    return x_data, y_datas, ref_x_data, ref_y_data


def time_plot(path: Path, *,
              normalize: bool = True):
    x_data, y_datas, ref_x_data, ref_y_data = _extract_x_data_and_y_datas(path)

    ### Time #######################################################################################
    title = 'Normalized Mass Over Time' if normalize else 'Mass Over Time'
    _time_plot(title, x_data, y_datas, ref_x_data, ref_y_data,
               normalize=normalize)

def measure_noise(path: Path):
    x_data, y_datas, ref_x_data, ref_y_data = _extract_x_data_and_y_datas(path)
    trim_idx = 0
    max_val = 1324900
    min_val = 1287000

    summed_channel_data = list()
    for idx in range(trim_idx, trim_idx + len(y_datas[0][trim_idx:])):
        total = 0
        for y_data in y_datas:
            total -= y_data[idx]
        summed_channel_data.append(total)

    noise_count = 0
    for val in summed_channel_data:
        if val > max_val or val < min_val:
            noise_count += 1
    signal_count = len(summed_channel_data) - noise_count
    print(f'signal count / noise count: {signal_count} / {noise_count}: '
          f'{noise_count/sum(summed_channel_data)*100}')

    plt.plot(x_data[trim_idx:], summed_channel_data, marker='.')
    plt.show()

def single_channel(path: Path):
    x_data, y_datas, ref_x_data, ref_y_data = _extract_x_data_and_y_datas(path)

    y_data = y_datas[0]
    noise_count = 0
    signal_count = 0
    for point in y_data:
        if point < -670000 or point > -350000:
            noise_count += 1
        else:
            signal_count += 1

    print(f'Error Rate %: ({noise_count}/{signal_count})*100 = '
          f'{(noise_count/signal_count)*100}%')

    plt.plot(x_data, y_data)
    plt.show()

def _time_plot(title: str,
               timestamps: list[datetime], channel_datas: list[list[int]],
               ref_timestamps: Optional[list[datetime]], ref_scale_data: Optional[list[int]],
               *,
               normalize: bool = True,
               invert_sum: bool = False,
               sensor_labels: Optional[list] = None):
    fig: plt.Figure = plt.figure(figsize=(21,17))
    ax = fig.add_subplot(111)
    ax.plot()
    # noinspection PyTypeHints
    ax.xaxis: Axis
    ax.xaxis.set_major_formatter(mdates.DateFormatter(timestamp.FMT))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=5))
    ax.tick_params(axis='x', labelrotation=90)

    x_ticks = [timestamps[idx] for idx in range(0, len(timestamps), len(timestamps)//9)]
    x_tick_labels = [timestamp.get_utc_iso_ts_str(dt) for dt in x_ticks]

    summed_channel_data = list()
    for idx in range(len(channel_datas[0])):
        total = 0
        for channel_data in channel_datas:
            if invert_sum:
                total -= channel_data[idx]
            else:
                total += channel_data[idx]
        summed_channel_data.append(total)


    # Filter for particle board prototype
    # Commented out 2025_04_02
    indices_to_remove = list()
    # for idx, value in enumerate(summed_channel_data):
    #     if value > 971400 or value < 805800:
    #         indices_to_remove.append(idx)
    # for idx in reversed(indices_to_remove):
    #     for channel_data in channel_datas:
    #         del channel_data[idx]
    #     del summed_channel_data[idx]
    #     del timestamps[idx]

    # Plot
    # mass_a, mass_b, mass_total = channel_datas[0:3]
    #
    # if len(channel_datas) >= 4:
    #     temperature = channel_datas[3]
    # else:
    #     temperature = None
    #
    # diff = list()
    # for mass_idx, mass in enumerate(mass_a):
    #     diff.append(mass - mass_total[mass_idx])
    #
    # plt.plot(timestamps, mass_a, label=f'Mass A')
    # plt.plot(timestamps, list(map(lambda x:-x, mass_b)), label=f'-Mass B')
    # plt.plot(timestamps, diff, label='diff')
    # plt.plot(timestamps, mass_total, label=f'Total Mass')
    # if temperature is not None:
    #     plt.plot(timestamps, temperature, label=f'Temperature')

    if sensor_labels is None:
        sensor_labels = [f'Sensor {idx}' for idx in range(len(channel_datas))]

    for sensor_idx, y_data in enumerate(channel_datas):
        plt.plot(timestamps,
                 normalize_list(y_data) if normalize else y_data,
                 label=sensor_labels[sensor_idx])
    # plt.plot(timestamps,
    #          normalize_list(summed_channel_data) if normalize else summed_channel_data,
    #          marker='.', label='Sum')
    if ref_timestamps:
        plt.plot(ref_timestamps,
                 normalize_list(ref_scale_data) if normalize else ref_scale_data,
                 marker='o', label='Reference')
    plt.legend()

    ax.set_xticks(x_ticks, x_tick_labels, rotation=90)
    if normalize:
        plt.ylabel('normalized mass')
    else:
        plt.ylabel('mass (grams)')
    plt.title(title)
    fig.tight_layout()
    # plt.subplots_adjust(bottom=.3)
    plt.show()

def thermal_test(path: Path, normalize=False):

    x_data, y_datas, _, __ = _extract_x_data_and_y_datas(path)

    ### Time Plot ##################################################################################
    _time_plot('Thermal Cycle Test', x_data, y_datas, None, None, normalize=normalize,
               sensor_labels=['Mass', 'Temperature'])

    ### Linearity ##################################################################################
    fig: plt.Figure = plt.figure()
    if normalize:
        lin_x = normalize_list(y_datas[0])
        lin_y = normalize_list(y_datas[1])
    else:
        lin_x = y_datas[0]
        lin_y = y_datas[1]

    plt.plot(lin_x, lin_y, marker='.', linestyle='-')
    step = 25
    for i in range(0, len(lin_x) - step, step):
        dy = lin_y[i+step] - lin_y[i]
        if dy > 0:
            dy = 1
        if dy < 0:
            dy = -1
        plt.quiver(lin_x[i], lin_y[i], 0.001, dy,
                  headwidth=2, headlength=5, color='black')

    fig.tight_layout()
    plt.show()

def bucket_test(path: Path, *,
                invert_sum: bool = False):
    x_data, y_datas, ref_x_data, ref_y_data = _extract_x_data_and_y_datas(path)

    ### Time #######################################################################################
    title = ('Experiment: Water bowl fill/empty 2 times.\n'
             'Test scale: 3d print load cell mounts glued to 20"x10" tray.\n'
             'Context: Concrete floor, reference scale in stack, centered mass.')
    _time_plot(title, x_data, y_datas, ref_x_data, ref_y_data, invert_sum=invert_sum)

    ### Linearity ##################################################################################
    fig: plt.Figure = plt.figure()
    summed_channel_data = list()
    for idx in range(len(y_datas[0])):
        total = 0
        for channel_data in y_datas:
            if invert_sum:
                total -= channel_data[idx]
            else:
                total += channel_data[idx]
        summed_channel_data.append(total)

    test_y_data = list()
    for ref_x, ref_y in zip(ref_x_data, ref_y_data):
        for test_x, test_y in zip(x_data, summed_channel_data):
            if ref_x == test_x:
                test_y_data.append(test_y)

    lin_x = normalize_list(ref_y_data)
    lin_y = normalize_list(test_y_data)
    plt.plot(lin_x, lin_y, marker='.', linestyle='-')
    for i in range(len(lin_x) - 1):
        dy = lin_y[i+1] - lin_y[i]
        if dy > 0:
            dy = 1
        if dy < 0:
            dy = -1
        plt.quiver(lin_x[i], lin_y[i], 0.001, dy,
                  headwidth=2, headlength=5, color='black')

    plt.title('Test scale vs. reference scale\n(0g - ~5kg)')
    plt.ylabel(f'Normalized test scale mass')
    plt.xlabel('Normalized reference scale mass')

    fig.tight_layout()
    plt.show()

    ### Error ######################################################################################
    error_x_data = ref_y_data
    difference_y_data = list()
    for ref_data, load_cell_data in (zip(lin_x, lin_y)):
        difference_y_data.append((load_cell_data-ref_data)*100)

    plt.plot(error_x_data, difference_y_data, marker='.', linestyle='-')
    for i in range(len(error_x_data) - 1):
        dy = lin_y[i+1] - lin_y[i]
        if dy > 0:
            dy = 1
        if dy < 0:
            dy = -1
        plt.quiver(error_x_data[i], difference_y_data[i], 0.001, dy,
                  headwidth=2, headlength=5, color='black')
    plt.title('% Error vs. reference scale mass')
    plt.ylabel('% error')
    plt.xlabel('Reference mass (grams)')
    fig.tight_layout()
    plt.show()

def csv_difference(path: Optional[Path] = None):
    if path is None:
        path = Path('/home/meyer/tmp/data.csv')
    x_data, y_datas = _extract_x_data_and_y_datas(path)
    load_cell_y_data, kitchen_scale_y_data = y_datas

    difference_y_data = list()
    multiplier_y_data = list()
    error_y_data = list()

    filtered_x_data = list()
    filtered_load_cell_y_data = list()
    filtered_kitchen_scale_y_data = list()

    for x_point, load_cell_point, kitchen_scale_point in (
            zip(x_data, load_cell_y_data, kitchen_scale_y_data)):
        if kitchen_scale_point is not None:
            difference_y_data.append(load_cell_point - kitchen_scale_point)
            if kitchen_scale_point == 0:
                multiplier_y_data.append(0)
            else:
                multiplier_y_data.append(load_cell_point / kitchen_scale_point)
            error_y_data.append(((load_cell_point - kitchen_scale_point)/kitchen_scale_point) * 100)
            filtered_x_data.append(x_point)
            filtered_load_cell_y_data.append(load_cell_point)
            filtered_kitchen_scale_y_data.append(kitchen_scale_point)

    fig: plt.Figure = plt.figure()
    ax = fig.add_subplot(111)
    # noinspection PyTypeHints
    ax.xaxis: Axis
    # ax.xaxis.set_major_formatter(mdates.DateFormatter(timestamp.FMT))
    # ax.xaxis.set_major_locator(mdates.DayLocator(interval=5))
    # ax.tick_params(axis='x', labelrotation=90)

    # plt.plot(filtered_x_data, difference_y_data)
    # plt.plot(filtered_x_data, filtered_load_cell_y_data, marker='.')
    # plt.plot(filtered_x_data, filtered_kitchen_scale_y_data, marker='.')
    # plt.plot(filtered_kitchen_scale_y_data, multiplier_y_data, marker='.')
    plt.plot(filtered_kitchen_scale_y_data, error_y_data, marker='.')

    for i in range(len(filtered_x_data) - 1):
        dy = filtered_kitchen_scale_y_data[i+1] - filtered_kitchen_scale_y_data[i]
        if dy > 0:
            dy = 1
        if dy < 0:
            dy = -1
        plt.quiver(filtered_kitchen_scale_y_data[i], error_y_data[i], 0.001, dy,
                  headwidth=2, headlength=5, color='black')

    # x_ticks = [filtered_x_data[idx] for idx in range(0,len(filtered_x_data),
    #                                                  len(filtered_x_data)//9)]
    # x_tick_labels = [timestamp.get_utc_iso_ts_str(dt) for dt in x_ticks]
    # ax.set_xticks(x_ticks, x_tick_labels, rotation=90)
    fig.tight_layout()
    plt.show()

    print(f'average: {sum(multiplier_y_data)/len(multiplier_y_data)}')

def main2():
    import matplotlib.pyplot as plt
    import numpy as np

    # Define dimensions
    Nx, Ny, Nz = 100, 300, 500
    X, Y, Z = np.meshgrid(np.arange(Nx), np.arange(Ny), -np.arange(Nz))

    # Create fake data
    data = (((X + 100) ** 2 + (Y - 20) ** 2 + 2 * Z) / 1000 + 1)

    kw = {
        'vmin': data.min(),
        'vmax': data.max(),
        'levels': np.linspace(data.min(), data.max(), 10),
    }

    # Create a figure with 3D ax
    fig = plt.figure(figsize=(5, 4))
    ax = fig.add_subplot(111, projection='3d')

    # Plot contour surfaces
    _ = ax.contourf(
        X[:, :, 0], Y[:, :, 0], data[:, :, 0],
        zdir='z', offset=0, **kw
    )
    _ = ax.contourf(
        X[0, :, :], data[0, :, :], Z[0, :, :],
        zdir='y', offset=0, **kw
    )
    C = ax.contourf(
        data[:, -1, :], Y[:, -1, :], Z[:, -1, :],
        zdir='x', offset=X.max(), **kw
    )
    # --

    # Set limits of the plot from coord limits
    xmin, xmax = X.min(), X.max()
    ymin, ymax = Y.min(), Y.max()
    zmin, zmax = Z.min(), Z.max()
    ax.set(xlim=[xmin, xmax], ylim=[ymin, ymax], zlim=[zmin, zmax])

    # Plot edges
    edges_kw = dict(color='0.4', linewidth=1, zorder=1e3)
    ax.plot([xmax, xmax], [ymin, ymax], 0, **edges_kw)
    ax.plot([xmin, xmax], [ymin, ymin], 0, **edges_kw)
    ax.plot([xmax, xmax], [ymin, ymin], [zmin, zmax], **edges_kw)

    # Set labels and zticks
    ax.set(
        xlabel='X [km]',
        ylabel='Y [km]',
        zlabel='Z [m]',
        zticks=[0, -150, -300, -450],
    )

    # Set zoom and angle view
    ax.view_init(40, -30, 0)
    ax.set_box_aspect(None, zoom=0.9)

    # Colorbar
    fig.colorbar(C, ax=ax, fraction=0.02, pad=0.1, label='Name [units]')

    # Show Figure
    plt.show()

def resister_divider():
    import matplotlib.pyplot as plt
    import numpy as np

    root = tk.Tk()

    # generate 2 2d grids for the x & y bounds
    # y, x = np.meshgrid(np.linspace(0, 10000, 1000),
    y, x = np.meshgrid(np.linspace(80, 120, 1000),
                       np.linspace(0, 1500, 1000))

    z = (5*y)/(x+y)
    # z = (1 - x / 2. + x ** 5 + y ** 3) * np.exp(-x ** 2 - y ** 2)
    # x and y are bounds, so z should be the value *inside* those bounds.
    # Therefore, remove the last value from the z array.
    z = z[:-1, :-1]

    fig, ax = plt.subplots()
    ax: matplotlib.axis

    z_min = 0
    z_max = 5

    c = ax.pcolormesh(x, y, z, cmap='RdBu', vmin=z_min, vmax=z_max)
    ax.set_title('pcolormesh')
    # set the limits of the plot to the limits of the data
    ax.axis([x.min(), x.max(), y.min(), y.max()])

    ax.set_xlabel('R1')
    ax.set_ylabel('R2')
    c_bar = fig.colorbar(c, ax=ax, )
    c_bar.set_label('Vo')

    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.draw()
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    y_min = y.min()
    y_max = y.max()

    def on_move(event):
        if event.inaxes:
            x, y = event.xdata, event.ydata
            z = (z_max*y)/(x+y)
            zmin = (z_max * y_min)/(x+y_min)
            zmax = (z_max * y_max)/(x+y_max)
            print(f'R1={x:.02f},R2={y:.02f},Vo={z:.02f},VoMin={zmin:.02f},VoMax={zmax:.02f},VoDelta'
                  f'={(zmax-zmin):.02f}')
            # # Create crosshair lines
            # ax.axvline(x, color='red', linewidth=0.5)
            # ax.axhline(y, color='red', linewidth=0.5)
            # ax.lines[-2:].remove()
            # ax.lines.clear()
            # print(ax.lines)
            # canvas.draw()

    def on_leave(event):
        # Remove crosshair lines when mouse leaves the axes
        # ax.lines[-2:].remove()
        canvas.draw()

    def on_closing():
        root.quit()
        root.destroy()

    # Connect events to canvas
    canvas.mpl_connect('motion_notify_event', on_move)
    canvas.mpl_connect('axes_leave_event', on_leave)
    root.protocol("WM_DELETE_WINDOW", on_closing)

    # Create the toolbar
    toolbar = NavigationToolbar2Tk(canvas, root)
    toolbar.update()

    # Run the Tkinter event loop
    root.mainloop()
    print('exited')

    # plt.show()

def velo_vs_scale():
    path = '/home/meyer/tmp/corrected_by_hand_scale_mm.csv'
    x_axis = list()
    y_axis = list()

    with open(path, 'r') as inf:
        lines = list(inf.readlines())
        _, x_title, y_title = lines[0].split(',')
        for line in lines[1:]:
            filename_root, scale_data, mm_data = line.split(',')
            if mm_data == '0' or scale_data == '0':
                continue

            mm_data = float(mm_data.strip())
            scale_data = int(scale_data.strip())

            if mm_data < 1.0:
                continue

            if scale_data > 5000:
                continue

            y_axis.append(mm_data)
            x_axis.append(scale_data)

    fig: plt.Figure = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot()

    # noinspection PyTypeHints
    ax.xaxis: Axis
    # noinspection PyTypeHints
    ax.yaxis: Axis
    ax.xaxis.set_label_text(x_title)
    ax.yaxis.set_label_text(y_title)
    print(mm_data)
    plt.plot(x_axis, y_axis, marker='.', linestyle='-')
    for i in range(len(x_axis) - 1):
        dx = x_axis[i+1] - x_axis[i]
        dy = y_axis[i+1] - y_axis[i]
        plt.quiver(x_axis[i], y_axis[i], dx, dy,
                  headwidth=3, headlength=5, color='black')
    plt.grid(True)
    plt.title('Velostat (2x), 12ga copper loop, inverted lids, 5V, R1=220ohm')
    plt.show()
