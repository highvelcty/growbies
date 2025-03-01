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

def _extract_x_data_and_y_datas(path: Path) -> tuple[list[datetime],list[list[Optional[int]]]]:
    labels = None
    x_data: list[datetime] = []
    y_datas: list[list[Optional[int]]] = []
    with open(path, 'r') as inf:
        for line in inf.readlines():
            if labels is None:
                labels = line.split(',')
                y_datas.extend(([] for _ in range(len(labels) - 1)))
            else:
                data = line.split(',')
                dt = timestamp.get_utc_dt(data[0])
                x_data.append(dt)
                for channel, channel_data in enumerate(data[1:]):
                    channel_data = channel_data.strip()

                    if len(y_datas) < channel + 1:
                        y_datas.append([])
                    if channel_data is None or channel_data == '':
                        y_datas[channel].append(None)
                    else:
                        y_datas[channel].append(int(channel_data))
    return x_data, y_datas

def csv(path: Optional[Path] = None):
    if path is None:
        path = Path('/home/meyer/tmp/data.csv')
    x_data, y_datas = _extract_x_data_and_y_datas(path)

    fig: plt.Figure = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot()
    # noinspection PyTypeHints
    ax.xaxis: Axis
    ax.xaxis.set_major_formatter(mdates.DateFormatter(timestamp.FMT))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=5))
    ax.tick_params(axis='x', labelrotation=90)

    x_ticks = [x_data[idx] for idx in range(0,len(x_data), len(x_data)//9)]
    x_tick_labels = [timestamp.get_utc_iso_ts_str(dt) for dt in x_ticks]

    # plt.plot(x_data, y_datas[0])
    # ax.set_xticks(x_ticks, x_tick_labels, rotation=90)
    # fig.tight_layout()
    # plt.show()


    cleaned_ydata_1 = list()
    for value in y_datas[1]:
        if value is None:
            cleaned_ydata_1.append(0)
        else:
            cleaned_ydata_1.append(value)
    ydata_0_norm = normalize_list(y_datas[0])
    ydata_1_norm = normalize_list(cleaned_ydata_1)
    uncleaned_ydata_1 = [None if data==0 else data for data in ydata_1_norm]
    plt.plot(x_data, ydata_0_norm)
    plt.plot(x_data, uncleaned_ydata_1, marker='o')
    # plt.plot(x_data, y_datas[1], marker='o')
    ax.set_xticks(x_ticks, x_tick_labels, rotation=90)
    plt.ylabel('normalized weight')
    plt.title('Experiment: Water bowl fill/empty 2 times\n'
              'Test scale: single load cell, double e-block\n'
              'full Wheatstone bridge.')
              # 'single load cell, double e-block on concrete')
    fig.tight_layout()
    plt.show()

    kitchen_x_data = list()
    load_cell_y_data = list()
    for data_0, data_1 in zip(ydata_0_norm, uncleaned_ydata_1):
        if data_1 is not None:
            kitchen_x_data.append(data_0)
            load_cell_y_data.append(data_1)

    plt.plot(kitchen_x_data, load_cell_y_data, marker='.', linestyle='-')
    for i in range(len(kitchen_x_data) - 1):
        dy = load_cell_y_data[i+1] - load_cell_y_data[i]
        if dy > 0:
            dy = 1
        if dy < 0:
            dy = -1
        plt.quiver(kitchen_x_data[i], load_cell_y_data[i], 0.001, dy,
                  headwidth=2, headlength=5, color='black')

    plt.title('Test scale vs. reference scale\n(~100g - ~4kg)')
    plt.ylabel(f'Normalized test scale mass')
    plt.xlabel('Normalized reference scale mass')

    fig.tight_layout()
    plt.show()

    difference_y_data = list()
    for kitchen_data, load_cell_data in (zip(kitchen_x_data, load_cell_y_data)):
        difference_y_data.append((load_cell_data-kitchen_data)*100)

    plt.plot(kitchen_x_data, difference_y_data, marker='.', linestyle='-')
    for i in range(len(kitchen_x_data) - 1):
        dy = load_cell_y_data[i+1] - load_cell_y_data[i]
        if dy > 0:
            dy = 1
        if dy < 0:
            dy = -1
        plt.quiver(kitchen_x_data[i], difference_y_data[i], 0.001, dy,
                  headwidth=2, headlength=5, color='black')
    plt.title('% Error vs. normalized reference scale mass\n'
              '(~100g - ~4kg)')
    plt.ylabel('% error')
    plt.xlabel('normalized reference scale mass')
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
