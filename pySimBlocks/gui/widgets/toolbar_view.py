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

from __future__ import annotations

from PySide6.QtWidgets import QToolBar, QMessageBox, QProgressDialog, QApplication
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt

from pySimBlocks.gui.dialogs.display_yaml_dialog import DisplayYamlDialog
from pySimBlocks.gui.dialogs.plot_dialog import PlotDialog
from pySimBlocks.gui.dialogs.settings_dialog import SettingsDialog
from pySimBlocks.gui.project_controller import ProjectController
from pySimBlocks.gui.services.project_saver import ProjectSaver
from pySimBlocks.gui.services.simulation_runner import SimulationRunner

# Add ons
from pySimBlocks.gui.addons.sofa.sofa_dialog import SofaDialog
from pySimBlocks.gui.addons.sofa.sofa_service import SofaService


class ToolBarView(QToolBar):
    """Application toolbar providing save, run, plot, and add-on actions.

    Attributes:
        saver: Service used to persist the project to disk.
        runner: Service used to launch a simulation.
        project_controller: Controller coordinating model and view mutations.
        sofa_service: Service managing SOFA-specific operations.
        sofa_action: Toolbar action for opening the SOFA dialog.
    """

    def __init__(
        self,
        saver: ProjectSaver,
        runner: SimulationRunner,
        project_controller: ProjectController,
    ):
        """Initialize the ToolBarView and register all toolbar actions.

        Args:
            saver: Service used to save the project to YAML.
            runner: Service used to launch a simulation.
            project_controller: Controller coordinating model and view mutations.

        Raises:
            None.
        """
        super().__init__()

        self.saver = saver
        self.runner = runner
        self.project_controller = project_controller

        save_action = QAction("Save", self)
        save_action.triggered.connect(self.on_save)
        self.addAction(save_action)

        export_action = QAction("Export", self)
        export_action.triggered.connect(self.on_export_project)
        self.addAction(export_action)

        display_action = QAction("Project YAML", self)
        display_action.triggered.connect(self.on_open_display_yaml)
        self.addAction(display_action)

        sim_settings_action = QAction("Settings", self)
        sim_settings_action.triggered.connect(self.on_open_simulation_settings)
        self.addAction(sim_settings_action)

        run_action = QAction("Run", self)
        run_action.triggered.connect(self.on_run_sim)
        self.addAction(run_action)

        plot_action = QAction("Plot", self)
        plot_action.triggered.connect(self.on_plot_logs)
        self.addAction(plot_action)

        # add ons
        self.sofa_service = SofaService(self.project_controller.project_state, self.project_controller)
        self.sofa_action = QAction("Sofa", self)
        self.sofa_action.triggered.connect(self.on_open_sofa_dialog)
        self.addAction(self.sofa_action)


    # --------------------------------------------------------------------------
    # Public Methods
    # --------------------------------------------------------------------------

    def on_save(self) -> None:
        """Save the project and clear the dirty flag."""
        self.saver.save(self.project_controller.project_state, self.project_controller.view.block_items)
        self.project_controller.clear_dirty()

    def on_export_project(self) -> None:
        """Prompt to save if dirty, then export the project."""
        window = self.parent()
        if window.confirm_discard_or_save("exporting"):
            self.saver.export(self.project_controller.project_state, self.project_controller.view.block_items)

    def on_open_display_yaml(self) -> None:
        """Open the YAML viewer dialog for the current project."""
        dialog = DisplayYamlDialog(self.project_controller.project_state, self.project_controller.view)
        dialog.exec()

    def on_open_simulation_settings(self) -> None:
        """Open the simulation settings dialog."""
        dialog = SettingsDialog(self.project_controller.project_state, self.project_controller, self.parent())
        dialog.exec()

    def on_run_sim(self) -> None:
        """Run the simulation with a busy progress dialog."""
        dlg = QProgressDialog(self)
        dlg.setWindowTitle("Simulation")
        dlg.setLabelText("Running simulation...\nPlease wait.")
        dlg.setRange(0, 0)  # busy indicator
        dlg.setCancelButton(None)
        dlg.setWindowModality(Qt.ApplicationModal)
        dlg.setMinimumWidth(300)
        dlg.setMinimumHeight(120)
        dlg.show()
        QApplication.processEvents()

        self.set_running(True)
        logs, flag, msg = self.runner.run(self.project_controller.project_state)
        dlg.close()
        self.set_running(False)
        self.project_controller.project_state.logs = logs

        if not flag:
            QMessageBox.warning(
                self,
                "Simulation failed with error",
                msg,
                QMessageBox.Ok,
            )

    def on_plot_logs(self) -> None:
        """Open the plot dialog if simulation logs are available."""
        flag, msg = self.project_controller.project_state.can_plot()
        if not flag:
            QMessageBox.warning(
                self,
                "Plot Error",
                msg,
                QMessageBox.Ok,
            )
            return
        self._plot_dialog = PlotDialog(self.project_controller.project_state, self.parent())  # keep ref because of python garbage collector
        self._plot_dialog.show()

    def set_running(self, running: bool) -> None:
        """Enable or disable all toolbar actions based on the running state.

        Args:
            running: True to disable all actions, False to re-enable them.
        """
        for action in self.actions():
            action.setEnabled(not running)

    def refresh_sofa_button(self) -> None:
        """Show or hide the SOFA toolbar button based on project contents."""
        if self.project_controller.has_sofa_block():
            if self.sofa_action not in self.actions():
                self.addAction(self.sofa_action)
        else:
            if self.sofa_action in self.actions():
                self.removeAction(self.sofa_action)

    def on_open_sofa_dialog(self) -> None:
        """Open the SOFA dialog if SOFA prerequisites are satisfied."""
        ok, msg, details = self.sofa_service.can_use_sofa()
        if not ok:
            QMessageBox.warning(
                self,
                msg,
                details,
                QMessageBox.Ok
            )
            return
        dialog = SofaDialog(self.sofa_service, self.parent())
        dialog.exec()
