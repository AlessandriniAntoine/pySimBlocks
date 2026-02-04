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

from PySide6.QtWidgets import (
    QWidget, QFormLayout, QLabel, QLineEdit, QComboBox,
    QListWidget, QListWidgetItem, QMessageBox
)
from PySide6.QtCore import Qt

from pySimBlocks.gui.model.project_state import ProjectState
from pySimBlocks.gui.project_controller import ProjectController


class SimulationSettingsWidget(QWidget):
    def __init__(self, project_state: ProjectState, project_controller: ProjectController):
        super().__init__()
        self.project_state = project_state
        self.project_controller = project_controller

        layout = QFormLayout(self)
        layout.addRow(QLabel("<b>Simulation Settings</b>"))

        self.dt_edit = QLineEdit(str(project_state.simulation.dt))
        layout.addRow("Step time:", self.dt_edit)

        self.solver_combo = QComboBox()
        self.solver_combo.addItems(["fixed", "variable"])
        self.solver_combo.setCurrentText(project_state.simulation.solver)
        layout.addRow("Solver:", self.solver_combo)

        self.T_edit = QLineEdit(str(project_state.simulation.T))
        layout.addRow("Stop time:", self.T_edit)

        # -------- Logs --------
        self.logs_list = QListWidget()
        self.logs_list.itemChanged.connect(self._on_log_changed)
        self._define_log_list()
        layout.addRow("Signals logged:", self.logs_list)

    def apply(self):

        params = {}
        try:
            params["dt"] = float(self.dt_edit.text())
        except ValueError:
            params["dt"] = self.dt_edit.text()
        try:
            params["T"] = float(self.T_edit.text())
        except ValueError:
            params["T"] = self.T_edit.text()
        params["solver"] = self.solver_combo.currentText()

        selected_signals = [
            self.logs_list.item(i).text()
            for i in range(self.logs_list.count())
            if self.logs_list.item(i).checkState() == Qt.Checked
        ]

        self.project_controller.update_simulation_params(params)
        self.project_controller.set_logged_signals(selected_signals)

    def refresh_from_project(self):
        """
        Synchronize the log checkbox list with project_state.logging.
        Called when the Simulation tab becomes active.
        """
        self._define_log_list()
        selected = set(self.project_state.logging)
        self.logs_list.blockSignals(True)

        for i in range(self.logs_list.count()):
            item = self.logs_list.item(i)
            should_be_checked = item.text() in selected
            item.setCheckState(
                Qt.Checked if should_be_checked else Qt.Unchecked
            )

        self.logs_list.blockSignals(False)

    def _define_log_list(self):
        self.logs_list.blockSignals(True)
        self.logs_list.clear()
        available = self.project_state.get_output_signals()
        selected = set(self.project_state.logging)
        for sig in available:
            item = QListWidgetItem(sig)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if sig in selected else Qt.Unchecked)
            self.logs_list.addItem(item)
        self.logs_list.blockSignals(False)

    def _on_log_changed(self, item: QListWidgetItem):
        if item.checkState() == Qt.Unchecked:
            used = any(
                item.text() in plot["signals"]
                for plot in self.project_state.plots
            )
            if used:
                QMessageBox.warning(
                    self,
                    "Signal in use",
                    f"The signal '{item.text()}' is used in a plot."
                )
                item.setCheckState(Qt.Checked)
