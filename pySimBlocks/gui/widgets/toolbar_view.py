from PySide6.QtWidgets import QToolBar, QMessageBox, QProgressDialog, QApplication
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt

from pySimBlocks.gui.dialogs.display_yaml_dialog import DisplayYamlDialog
from pySimBlocks.gui.dialogs.plot_dialog import PlotDialog
from pySimBlocks.gui.dialogs.settings_dialog import SettingsDialog
from pySimBlocks.gui.model.project_state import ProjectState
from pySimBlocks.gui.services.project_controller import ProjectController

# Add ons
from pySimBlocks.gui.addons.sofa.sofa_dialog import SofaDialog
from pySimBlocks.gui.addons.sofa.sofa_service import SofaService


class ToolBarView(QToolBar):

    def __init__(self, project_state: ProjectState, project_controller: ProjectController):
        super().__init__()

        self.project_state = project_state
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

        # add ons
        self.sofa_service = SofaService(self.project_state, self.project_controller)
        self.sofa_action = QAction("Sofa", self)
        self.sofa_action.triggered.connect(self.open_sofa_dialog)
        self.addAction(self.sofa_action)

    def save_yaml(self):
        self.project_controller.save()

    def export_project(self):
        self.project_controller.export()

    def open_display_yaml(self):
        dialog = DisplayYamlDialog(self.project_state, self.project_controller.view)
        dialog.exec()

    def open_simulation_settings(self):
        dialog = SettingsDialog(self.project_state, self.project_controller)
        dialog.exec()

    def run_sim(self):
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
        logs, flag, msg = self.project_controller.run()
        dlg.close()
        self.set_running(False)
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


    def set_running(self, running: bool):
        for action in self.actions():
            action.setEnabled(not running)

    #####################################
    # Adds on
    def refresh_sofa_button(self):
        if self.project_state.has_sofa_block():
            if self.sofa_action not in self.actions():
                self.addAction(self.sofa_action)
        else:
            if self.sofa_action in self.actions():
                self.removeAction(self.sofa_action)

    def open_sofa_dialog(self):
        ok, msg, details = self.sofa_service.can_use_sofa()
        if not ok:
            QMessageBox.warning(
                self,
                msg,
                details,
                QMessageBox.Ok
            )
            return
        dialog = SofaDialog(self.sofa_service)
        dialog.exec()
