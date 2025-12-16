import numpy as np
import matplotlib.pyplot as plt

from pySimBlocks.core.config import PlotConfig


def plot_from_config(
    logs: dict,
    plot_cfg: PlotConfig | None,
    show: bool = True,
):
    """
    Plot logged simulation signals according to a PlotConfig.

    Parameters
    ----------
    logs : dict
        Logs returned by Simulator.run().
        Must contain 'time' and all requested signals.

    plot_cfg : PlotConfig
        Plot description (titles, signals to plot).

    show : bool, optional
        Whether to call plt.show() at the end (default: True).
    """

    if plot_cfg is None:
        return

    time = np.asarray(logs["time"]).flatten()
    length = len(time)

    for plot in plot_cfg.plots:
        title = plot.get("title", "")
        signals = plot["signals"]

        plt.figure()

        for sig in signals:
            if sig not in logs:
                raise KeyError(
                    f"Signal '{sig}' not found in logs. "
                    f"Available signals: {list(logs.keys())}"
                )

            data = np.asarray(logs[sig]).reshape(length, -1)

            # If vector signal, plot each component
            for i in range(data.shape[1]):
                label = sig if data.shape[1] == 1 else f"{sig}[{i}]"
                plt.step(time, data[:, i], where="post", label=label)

        plt.xlabel("Time [s]")
        plt.grid(True)
        plt.legend()

        if title:
            plt.title(title)

    if show:
        plt.show()
