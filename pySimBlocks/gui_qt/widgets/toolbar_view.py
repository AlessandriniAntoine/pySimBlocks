import os
import shutil
from PySide6.QtWidgets import QToolBar, QMessageBox
from PySide6.QtGui import QAction

from pySimBlocks.gui_qt.dialogs.display_yaml_dialogs import DisplayYamlDialog
from pySimBlocks.gui_qt.model.project_state import ProjectState
from pySimBlocks.gui_qt.dialogs.settings import SettingsDialog
from pySimBlocks.gui_qt.yaml_tools import save_yaml
from pySimBlocks.project.generate_run_script import generate_python_content



class ToolBarView(QToolBar):

    def __init__(self, project: ProjectState):
        super().__init__()

        self.project_state = project

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
        save_yaml(self.project_state)

    def export_project(self):
        save_yaml(self.project_state)
        run_py = self.project_state.directory_path / "run.py"
        run_py.write_text(
            generate_python_content(
                model_yaml_path="model.yaml",
                parameters_yaml_path="parameters.yaml"
            )
        )

    def open_display_yaml(self):
        dialog = DisplayYamlDialog(self.project_state)
        dialog.exec()

    def open_simulation_settings(self):
        dialog = SettingsDialog(self.project_state)
        dialog.exec()

    def run_sim(self):
        project_dir = self.project_state.directory_path
        if project_dir is None:
            return

        temp_dir = project_dir / ".temp"

        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        temp_dir.mkdir(parents=True)
        save_yaml(self.project_state, True)

        model_path = temp_dir / "model.yaml"
        param_path = temp_dir / "parameters.yaml"

        code = generate_python_content(
            model_yaml_path=str(model_path),
            parameters_yaml_path=str(param_path),
            enable_plots=False
        )

        old_cwd = os.getcwd()
        try:
            env = {}
            os.chdir(temp_dir)

            exec(code, env, env)

            logs = env.get("logs")
            if logs is None:
                raise RuntimeError("Simulation did not produce logs")
            self.project_state.logs = logs

        except Exception as e:
            return False

        finally:
            os.chdir(old_cwd)


    def plot_logs(self):
        logs_keys = self.project_state.logs.keys()
        plots = self.project_state.plots
        if len(logs_keys) == 0:
            QMessageBox.warning(
                self,
                "No simulation",
                f"The simulation has not been done yet.\nPlease click on Run.",
                QMessageBox.Ok,
            )
            return
        elif len(plots) == 0:
            QMessageBox.warning(
                self,
                "No plots asked",
                f"Simulation has been done but no plots set.\nPlease create plots on settings.",
                QMessageBox.Ok,
            )
            return
