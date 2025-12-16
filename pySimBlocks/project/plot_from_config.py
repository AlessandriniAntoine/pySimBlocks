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

    plot_cfg : PlotConfig | None
        Plot description (titles, signals to plot).
        If None, this function does nothing.

    show : bool, optional
        Whether to call plt.show() at the end (default: True).
    """

    if plot_cfg is None:
        return

    # ------------------------------------------------------------
    # Global validation: all plotted signals must be logged
    # ------------------------------------------------------------
    requested_signals = set()
    for plot in plot_cfg.plots:
        requested_signals.update(plot["signals"])

    available_signals = set(logs.keys())
    available_signals.discard("time")

    missing = sorted(requested_signals - available_signals)
    if missing:
        raise KeyError(
            "The following signals are requested for plotting but were not logged:\n"
            + "\n".join(f"  - {sig}" for sig in missing)
            + "\n\nAvailable logged signals:\n"
            + "\n".join(f"  - {sig}" for sig in sorted(available_signals))
        )

    # ------------------------------------------------------------
    # Plotting
    # ------------------------------------------------------------
    time = np.asarray(logs["time"]).flatten()
    length = len(time)

    for plot in plot_cfg.plots:
        title = plot.get("title", "")
        signals = plot["signals"]

        plt.figure()

        for sig in signals:
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
