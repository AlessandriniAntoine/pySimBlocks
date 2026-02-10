# ******************************************************************************
#                                  pySimBlocks
#                     Copyright (c) 2026 Université de Lille & INRIA
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

from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QVBoxLayout,
    QLabel, QListWidget, QListWidgetItem,
    QPushButton, QSizePolicy, QMessageBox
)
from PySide6.QtCore import Qt

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from pySimBlocks.gui.model.project_state import ProjectState
from pySimBlocks.core.config import PlotConfig
from pySimBlocks.project.plot_from_config import plot_from_config


class PlotDialog(QDialog):
    def __init__(self, project_state: ProjectState, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Plot signals")
        self.resize(900, 500)

        self.project_state = project_state
        self.selected_signals: set[str] = set()

        self._build_ui()
        self._populate_signals()

    # ------------------------------------------------------------
    # UI
    # ------------------------------------------------------------
    def _build_ui(self):
        main_layout = QHBoxLayout(self)

        # ---------- Left panel ----------
        left_layout = QVBoxLayout()

        title = QLabel("<b>Signals (logged)</b>")
        left_layout.addWidget(title)

        self.signal_list = QListWidget()
        self.signal_list.setSelectionMode(QListWidget.NoSelection)
        self.signal_list.itemChanged.connect(self._on_signal_toggled)
        left_layout.addWidget(self.signal_list)

        self.plot_defined_btn = QPushButton("Plot defined plots")
        self.plot_defined_btn.clicked.connect(self._plot_defined_plots)
        left_layout.addWidget(self.plot_defined_btn)

        main_layout.addLayout(left_layout, 0)

        # ---------- Plot preview ----------
        self.figure = Figure()
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        main_layout.addWidget(self.canvas, 1)

    # ------------------------------------------------------------
    # Populate signals
    # ------------------------------------------------------------
    def _populate_signals(self):
        self.signal_list.clear()

        for sig in sorted(self.project_state.logs.keys()):
            if sig == "time":
                continue

            item = QListWidgetItem(sig)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.signal_list.addItem(item)

    # ------------------------------------------------------------
    # Interactive plot
    # ------------------------------------------------------------
    def _on_signal_toggled(self, item: QListWidgetItem):
        sig = item.text()

        if item.checkState() == Qt.Checked:
            self.selected_signals.add(sig)
        else:
            self.selected_signals.discard(sig)

        self._update_preview_plot()


    def _stack_logged_signal_2d(self, sig: str) -> np.ndarray:
        """
        Stack a logged signal over time, preserving its 2D shape.

        Returns:
            data: np.ndarray of shape (T, m, n)

        Raises:
            ValueError if samples are not 2D arrays of consistent shape.
        """
        samples = self.project_state.logs.get(sig, None)
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

        return np.stack(stacked, axis=0)  # (T, m, n)


    def _update_preview_plot(self):
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        if not self.selected_signals:
            self.canvas.draw()
            return

        time = np.asarray(self.project_state.logs["time"]).flatten()
        T = len(time)

        try:
            for sig in sorted(self.selected_signals):
                data = self._stack_logged_signal_2d(sig)  # (T, m, n)

                if data.shape[0] != T:
                    raise ValueError(
                        f"Time length mismatch for '{sig}': time has {T} samples but signal has {data.shape[0]}."
                    )

                m, n = data.shape[1], data.shape[2]

                # scalar
                if (m, n) == (1, 1):
                    ax.step(time, data[:, 0, 0], where="post", label=sig)
                    continue

                # vector column (m,1)
                if n == 1:
                    for i in range(m):
                        ax.step(time, data[:, i, 0], where="post", label=f"{sig}[{i}]")
                    continue

                # matrix (m,n)
                for r in range(m):
                    for c in range(n):
                        ax.step(time, data[:, r, c], where="post", label=f"{sig}[{r},{c}]")

            ax.set_xlabel("Time [s]")
            ax.grid(True)
            ax.legend()

        except Exception as e:
            # Keep the UI responsive; show the error inside the plot area.
            ax.text(
                0.01, 0.99,
                f"Plot preview error:\n{e}",
                transform=ax.transAxes,
                va="top",
                ha="left",
                wrap=True,
            )
            ax.set_axis_off()

        self.canvas.draw()

    # ------------------------------------------------------------
    # Plot defined plots (matplotlib windows)
    # ------------------------------------------------------------
    def _plot_defined_plots(self):
        if not self.project_state.plots:
            QMessageBox.information(
                self,
                "No plots defined",
                "No plots are defined in the project settings."
            )
            return

        plot_from_config(
            logs=self.project_state.logs,
            plot_cfg=PlotConfig(self.project_state.plots),
            show=True,
            block=False
        )
