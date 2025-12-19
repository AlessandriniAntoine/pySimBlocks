from pathlib import Path
from PySide6.QtWidgets import (
    QHBoxLayout,
    QDialog,
    QLabel,
    QVBoxLayout,
    QLineEdit,
    QPushButton,
    QFormLayout,
    QComboBox,
    QMessageBox
)

from pySimBlocks.gui_qt.model.project_state import ProjectState

class SettingsDialog(QDialog):
    def __init__(self, project:ProjectState, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Simulation Settings")
        self.setMinimumWidth(350)

        self.project_state = project

        main_layout = QVBoxLayout(self)
        self.build_project_form(main_layout)
        self.build_simulation_form(main_layout)
        self.build_plots_form(main_layout)
        self.build_buttons(main_layout)


    def build_project_form(self, layout):
        form = QFormLayout()
        title = QLabel("<b>Project Settings</b>")
        form.addRow(title)

        dir_path = self.project_state.directory_path
        self.dir_path_edit = QLineEdit(str(dir_path))
        form.addRow(QLabel("Directory path:"), self.dir_path_edit)

        layout.addLayout(form)

    def build_simulation_form(self, layout):
        form = QFormLayout()
        title = QLabel("<b>Simulation Settings</b>")
        form.addRow(title)
        dt = self.project_state.simulation.get("dt", 0.01)
        self.dt_edit = QLineEdit(str(dt))
        form.addRow(QLabel("Step time:"), self.dt_edit)

        self.solver_combo = QComboBox()
        self.solver_combo.addItems(["fixed", "variable"])
        self.solver_combo.setCurrentText(self.project_state.simulation.get("solver", "fixed"))
        form.addRow("Solver:", self.solver_combo)

        T = self.project_state.simulation.get("T", 10.)
        self.T_edit = QLineEdit(str(T))
        form.addRow(QLabel("Stop time:"), self.T_edit)

        external = self.project_state.external
        external = "" if external is None else external
        self.file_edit = QLineEdit(external)
        form.addRow(QLabel("Python File:"), self.file_edit)

        layout.addLayout(form)

    def build_plots_form(self, layout):
        form = QFormLayout()
        title = QLabel("<b>Plot Settings</b>")
        form.addRow(title)

        layout.addLayout(form)

    # ------------------------------------------------------------
    # Buttons
    def build_buttons(self, layout):
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        ok_btn = QPushButton("Ok")
        ok_btn.setDefault(True)
        ok_btn.setAutoDefault(True)
        ok_btn.clicked.connect(self.ok)
        buttons_layout.addWidget(ok_btn)

        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self.apply)
        buttons_layout.addWidget(apply_btn)

        layout.addLayout(buttons_layout)


    def apply(self):
        dir_path = Path(self.dir_path_edit.text())

        if not dir_path.exists():
            QMessageBox.warning(
                self,
                "Invalid directory",
                f"The directory does not exist:\n\n{dir_path}",
                QMessageBox.Ok,
            )
            return False

        # --- Simulation settings ---
        try:
            dt = float(self.dt_edit.text())
        except:
            dt = self.dt_edit.text()
        try:
            T = float(self.T_edit.text())
        except:
            T = self.T_edit.text()
        self.project_state.simulation["dt"] = dt
        self.project_state.simulation["solver"] = self.solver_combo.currentText()
        self.project_state.simulation["T"] = T


        # --- External file ---
        file = self.file_edit.text().strip()
        self.project_state.external = None if file == "" else file

        self.accept()
        return True


    def ok(self):
        msg = self.apply()
        if msg:
            self.reject()
