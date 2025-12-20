import os
import shutil
from PySide6.QtWidgets import QToolBar, QMessageBox
from PySide6.QtGui import QAction

from pySimBlocks.gui_qt.dialogs.display_yaml_dialog import DisplayYamlDialog
from pySimBlocks.gui_qt.dialogs.plot_dialog import PlotDialog
from pySimBlocks.gui_qt.dialogs.settings_dialog import SettingsDialog
from pySimBlocks.gui_qt.model.project_state import ProjectState
from pySimBlocks.gui_qt.services.project_controller import ProjectController


class ToolBarView(QToolBar):

    def __init__(self, project: ProjectState, project_controller: ProjectController):
        super().__init__()

        self.project_state = project
        self.project_controller = project_controller

        save_action = QAction("Save", self)
        save_action.triggered.connect(self.save_yaml)
        self.addAction(save_action)

        export_action = QAction("Export", self)
        export_action.triggered.connect(self.export_project)
        self.addAction(export_action)

        display_action = QAction("Display files", self)
        display_action.triggered.connect(self.open_display_yaml)
        self.addAction(display_action)

        sim_settings_action = QAction("Settings", self)
        sim_settings_action.triggered.connect(self.open_simulation_settings)
        self.addAction(sim_settings_action)

        run_action = QAction("Run", self)
        run_action.triggered.connect(self.run_sim)
        self.addAction(run_action)

        plot_action = QAction("Plot", self)
        plot_action.triggered.connect(self.plot_logs)
        self.addAction(plot_action)

    def save_yaml(self):
        self.project_controller.save()

    def export_project(self):
        self.project_controller.export()

    def open_display_yaml(self):
        dialog = DisplayYamlDialog(self.project_state)
        dialog.exec()

    def open_simulation_settings(self):
        dialog = SettingsDialog(self.project_state)
        dialog.exec()

    def run_sim(self):
        logs, flag, msg = self.project_controller.run()
        self.project_state.logs = logs
        if not flag:
            QMessageBox.warning(
                self,
                "Simulation failed with error",
                msg,
                QMessageBox.Ok,
            )


    def plot_logs(self):
        flag, msg = self.project_controller.can_plot()
        if not flag:
            QMessageBox.warning(
                self,
                "Plot Error",
                msg,
                QMessageBox.Ok,
            )
            return
        dialog = PlotDialog(self.project_state)
        dialog.exec()
