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

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTabWidget
)

from pySimBlocks.gui.dialogs.settings.project import ProjectSettingsWidget
from pySimBlocks.gui.dialogs.settings.simulation import SimulationSettingsWidget
from pySimBlocks.gui.dialogs.settings.plots import PlotSettingsWidget
from pySimBlocks.gui.models.project_state import ProjectState
from pySimBlocks.gui.project_controller import ProjectController


class SettingsDialog(QDialog):
    """Display project, simulation, and plot settings in a tabbed dialog.

    Attributes:
        tabs: Tab widget containing all settings pages.
        project_tab: Project settings widget.
        simulation_tab: Simulation settings widget.
        plots_tab: Plot settings widget.
    """

    def __init__(self, project_state: ProjectState, project_controller: ProjectController,  parent=None):
        """Initialize the settings dialog.

        Args:
            project_state: Project state edited by the dialog.
            project_controller: Controller applying the edited settings.
            parent: Optional parent widget.

        Raises:
            None.
        """
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)

        # ---------------- Tabs ----------------
        self.tabs = QTabWidget()
        self.project_tab = ProjectSettingsWidget(project_state, project_controller, self)
        self.simulation_tab = SimulationSettingsWidget(project_state, project_controller)
        self.plots_tab = PlotSettingsWidget(project_state, project_controller)

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

    # --------------------------------------------------------------------------
    # Public Methods
    # --------------------------------------------------------------------------

    def ok(self):
        """Apply settings and close the dialog."""
        self.apply()
        self.accept()

    def apply(self):
        """Apply the currently edited settings to the project."""
        if not self.project_tab.apply():
            return
        self.simulation_tab.apply()

    def refresh_tabs_from_project(self):
        """Refresh dependent tabs from the current project state."""
        self.simulation_tab.refresh_from_project()
        self.plots_tab.refresh_from_project()

    # --------------------------------------------------------------------------
    # Private Methods
    # --------------------------------------------------------------------------

    def _on_tab_changed(self, index):
        """Refresh the newly selected tab when it supports project syncing."""
        widget = self.tabs.widget(index)

        if hasattr(widget, "refresh_from_project"):
            widget.refresh_from_project()
