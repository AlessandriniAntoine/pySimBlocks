from PySide6.QtWidgets import (
    QWidget, QFormLayout, QLabel, QLineEdit, QComboBox,
    QListWidget, QListWidgetItem, QMessageBox
)
from PySide6.QtCore import Qt

from pySimBlocks.gui_qt.model.project_state import ProjectState


class SimulationSettingsWidget(QWidget):
    def __init__(self, project: ProjectState):
        super().__init__()
        self.project = project

        layout = QFormLayout(self)
        layout.addRow(QLabel("<b>Simulation Settings</b>"))

        self.dt_edit = QLineEdit(str(project.simulation.get("dt", 0.01)))
        layout.addRow("Step time:", self.dt_edit)

        self.solver_combo = QComboBox()
        self.solver_combo.addItems(["fixed", "variable"])
        self.solver_combo.setCurrentText(project.simulation.get("solver", "fixed"))
        layout.addRow("Solver:", self.solver_combo)

        self.T_edit = QLineEdit(str(project.simulation.get("T", 10.0)))
        layout.addRow("Stop time:", self.T_edit)

        # -------- Logs --------
        self.logs_list = QListWidget()
        self.logs_list.itemChanged.connect(self._on_log_changed)

        available = project.get_output_signals()
        selected = set(project.logging)

        for sig in available:
            item = QListWidgetItem(sig)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if sig in selected else Qt.Unchecked)
            self.logs_list.addItem(item)

        layout.addRow("Signals logged:", self.logs_list)

    def apply(self):
        try:
            self.project.simulation["dt"] = float(self.dt_edit.text())
        except ValueError:
            self.project.simulation["dt"] = self.dt_edit.text()

        try:
            self.project.simulation["T"] = float(self.T_edit.text())
        except ValueError:
            self.project.simulation["T"] = self.T_edit.text()

        self.project.simulation["solver"] = self.solver_combo.currentText()

        self.project.logging = [
            self.logs_list.item(i).text()
            for i in range(self.logs_list.count())
            if self.logs_list.item(i).checkState() == Qt.Checked
        ]

    def refresh_from_project(self):
        """
        Synchronize the log checkbox list with project_state.logging.
        Called when the Simulation tab becomes active.
        """
        selected = set(self.project.logging)

        # Block signals to avoid recursive itemChanged triggers
        self.logs_list.blockSignals(True)

        for i in range(self.logs_list.count()):
            item = self.logs_list.item(i)
            should_be_checked = item.text() in selected
            item.setCheckState(
                Qt.Checked if should_be_checked else Qt.Unchecked
            )

        self.logs_list.blockSignals(False)


    def _on_log_changed(self, item: QListWidgetItem):
        if item.checkState() == Qt.Unchecked:
            used = any(
                item.text() in plot["signals"]
                for plot in self.project.plots
            )
            if used:
                QMessageBox.warning(
                    self,
                    "Signal in use",
                    f"The signal '{item.text()}' is used in a plot."
                )
                item.setCheckState(Qt.Checked)
