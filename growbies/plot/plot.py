from datetime import datetime
from pathlib import Path
from growbies.utils import timestamp
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.axis import Axis
import matplotlib

matplotlib.use('TkAgg')

PATH_TO_CSV = Path('/home/meyer/tmp/2025-01-06T003152Z-first_experiment_with_tray_and_cup/data.csv')

def main():
    labels = None
    x_data: list[datetime] = []
    y_datas: list[list[int]] = []
    with open(PATH_TO_CSV, 'r') as inf:
        for line in inf.readlines():
            if labels is None:
                labels = line.split(',')
                y_datas.extend(([] for _ in range(len(labels) - 1)))
            else:
                data = line.split(',')
                dt = timestamp.get_utc_dt(data[0])
                x_data.append(dt)
                for channel, channel_data in enumerate(data[1:]):
                    if len(y_datas) < channel + 1:
                        y_datas.append([])
                    y_datas[channel].append(int(channel_data))

    fig: plt.Figure = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot()
    # noinspection PyTypeHints
    ax.xaxis: Axis
    ax.xaxis.set_major_formatter(mdates.DateFormatter(timestamp.FMT))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=5))
    ax.tick_params(axis='x', labelrotation=90)

    for y_data in y_datas:
        plt.plot(x_data, y_data)
    plt.show()


if __name__ == '__main__':
    main()