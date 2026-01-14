from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTabWidget
)

from pySimBlocks.gui.dialogs.settings.project import ProjectSettingsWidget
from pySimBlocks.gui.dialogs.settings.simulation import SimulationSettingsWidget
from pySimBlocks.gui.dialogs.settings.plots import PlotSettingsWidget
from pySimBlocks.gui.model.project_state import ProjectState
from pySimBlocks.gui.services.project_controller import ProjectController


class SettingsDialog(QDialog):
    def __init__(self, project_state: ProjectState, project_controller: ProjectController,  parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(500)

        self.project_state = project_state

        layout = QVBoxLayout(self)

        # ---------------- Tabs ----------------
        self.tabs = QTabWidget()
        self.project_tab = ProjectSettingsWidget(project_state, project_controller, self)
        self.simulation_tab = SimulationSettingsWidget(project_state)
        self.plots_tab = PlotSettingsWidget(project_state)

        self.tabs.addTab(self.project_tab, "Project")
        self.tabs.addTab(self.simulation_tab, "Simulation")
        self.tabs.addTab(self.plots_tab, "Plots")

        self.tabs.currentChanged.connect(self._on_tab_changed)

        layout.addWidget(self.tabs)

        # ---------------- Buttons ----------------
        buttons = QHBoxLayout()
        buttons.addStretch()

        ok_btn = QPushButton("Ok")
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(self.ok)

        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self.apply)

        buttons.addWidget(ok_btn)
        buttons.addWidget(apply_btn)

        layout.addLayout(buttons)

    def ok(self):
        self.apply()
        self.accept()

    def apply(self):
        if not self.project_tab.apply():
            return
        self.simulation_tab.apply()

    def refresh_tabs_from_project(self):
        self.simulation_tab.refresh_from_project()
        self.plots_tab.refresh_from_project()

    def _on_tab_changed(self, index):
        widget = self.tabs.widget(index)

        if hasattr(widget, "refresh_from_project"):
            widget.refresh_from_project()
