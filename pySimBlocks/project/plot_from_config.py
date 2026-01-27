# ******************************************************************************
#                                  pySimBlocks
#                     Copyright (c) 2026 Antoine Alessandrini
# ******************************************************************************
#  This program is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Lesser General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or (at your
#  option) any later version.
#
#  This program is distributed in the hope that it will be useful, but WITHOUT
#  ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
#  FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License
#  for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.
# ******************************************************************************
#  Authors: see Authors.txt
# ******************************************************************************

import numpy as np
import matplotlib.pyplot as plt

from pySimBlocks.core.config import PlotConfig


def _stack_logged_signal(logs: dict, sig: str) -> np.ndarray:
    """
    Stack a logged signal over time, preserving its 2D shape.

    Returns:
        data: np.ndarray of shape (T, m, n)

    Raises:
        ValueError: if the signal is not a list of 2D arrays with consistent shape.
    """
    samples = logs[sig]
    if not isinstance(samples, list) or len(samples) == 0:
        raise ValueError(f"Signal '{sig}' has no samples in logs.")

    # Find first non-None sample to define shape
    first = None
    for s in samples:
        if s is not None:
            first = np.asarray(s)
            break

    if first is None:
        raise ValueError(f"Signal '{sig}' is always None; cannot plot.")

    if first.ndim != 2:
        raise ValueError(f"Signal '{sig}' must be 2D. Got ndim={first.ndim} with shape {first.shape}.")

    shape0 = first.shape

    stacked = []
    for k, s in enumerate(samples):
        if s is None:
            raise ValueError(f"Signal '{sig}' contains None at index {k}; cannot plot.")
        a = np.asarray(s)
        if a.ndim != 2:
            raise ValueError(
                f"Signal '{sig}' sample {k} must be 2D. Got ndim={a.ndim} with shape {a.shape}."
            )
        if a.shape != shape0:
            raise ValueError(
                f"Signal '{sig}' shape changed over time: expected {shape0}, got {a.shape} at sample {k}."
            )
        stacked.append(a)

    data = np.stack(stacked, axis=0)  # (T, m, n)
    return data


def plot_from_config(
    logs: dict,
    plot_cfg: PlotConfig | None,
    show: bool = True,
    block: bool = True
):
    """
    Plot logged simulation signals according to a PlotConfig.

    Supports 2D signals:
      - scalar (1,1)
      - column vectors (n,1)
      - matrices (m,n) with n>1

    Plot semantics:
      - each component is plotted as a separate curve
      - labels:
          scalar:      sig
          vector:      sig[i]
          matrix:      sig[r,c]
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

    if "time" not in logs:
        raise KeyError("Logs must contain a 'time' entry.")

    # ------------------------------------------------------------
    # Time base
    # Your simulator logs time as np.array([t_step]) each step,
    # so flatten() is appropriate.
    # ------------------------------------------------------------
    time = np.asarray(logs["time"]).flatten()
    T = len(time)
    if T == 0:
        return

    # ------------------------------------------------------------
    # Plotting
    # ------------------------------------------------------------
    for plot in plot_cfg.plots:
        title = plot.get("title", "")
        signals = plot["signals"]

        plt.figure()

        for sig in signals:
            data = _stack_logged_signal(logs, sig)  # (T, m, n)

            if data.shape[0] != T:
                raise ValueError(
                    f"Time length mismatch for '{sig}': time has {T} samples but signal has {data.shape[0]}."
                )

            m, n = data.shape[1], data.shape[2]

            # scalar
            if (m, n) == (1, 1):
                plt.step(time, data[:, 0, 0], where="post", label=sig)
                continue

            # vector column (n,1) -> label sig[i]
            if n == 1:
                for i in range(m):
                    plt.step(time, data[:, i, 0], where="post", label=f"{sig}[{i}]")
                continue

            # matrix (m,n) -> label sig[r,c]
            for r in range(m):
                for c in range(n):
                    plt.step(time, data[:, r, c], where="post", label=f"{sig}[{r},{c}]")

        plt.xlabel("Time [s]")
        plt.grid(True)
        plt.legend()

        if title:
            plt.title(title)

    if show:
        plt.show(block=block)
