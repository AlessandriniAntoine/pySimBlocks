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


    def _update_preview_plot(self):
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        if not self.selected_signals:
            self.canvas.draw()
            return

        time = np.asarray(self.project_state.logs["time"]).flatten()
        n = len(time)

        for sig in sorted(self.selected_signals):
            data = np.asarray(self.project_state.logs[sig]).reshape(n, -1)

            for i in range(data.shape[1]):
                label = sig if data.shape[1] == 1 else f"{sig}[{i}]"
                ax.step(time, data[:, i], where="post", label=label)

        ax.set_xlabel("Time [s]")
        ax.grid(True)
        ax.legend()
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
        )
