from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QFormLayout, QLabel, QLineEdit, QMessageBox, QPushButton
)

from pySimBlocks.gui.model.project_state import ProjectState
from pySimBlocks.gui.services.project_controller import ProjectController


class ProjectSettingsWidget(QWidget):
    def __init__(self, project_state: ProjectState, project_controller: ProjectController, settings_dialg):
        super().__init__()
        self.project_state = project_state
        self.project_controller = project_controller
        self.settings_dialog = settings_dialg

        layout = QFormLayout(self)
        layout.addRow(QLabel("<b>Project Settings</b>"))

        self.dir_edit = QLineEdit(str(project_state.directory_path))
        layout.addRow("Directory path:", self.dir_edit)

        ext = project_state.external or ""
        self.external_edit = QLineEdit(ext)
        label = QLabel("Python file:")
        label.setToolTip("Relative path from project directory")
        layout.addRow(label, self.external_edit)

        load_btn = QPushButton("Load")
        load_btn.clicked.connect(self.load_project)
        label = QLabel("Load Project:")
        label.setToolTip("Auto Load project from directory with parameters and model yaml.")
        layout.addRow(label, load_btn)


    def apply(self) -> bool:
        path = Path(self.dir_edit.text())
        if not path.exists():
            QMessageBox.warning(
                self,
                "Invalid directory",
                f"The directory does not exist:\n{path}",
            )
            return False
        self.project_controller.change_project_directory(path)
        ext = self.external_edit.text().strip()
        self.project_state.external = None if ext == "" else ext
        return True

    def load_project(self):
        self.apply()
        self.project_controller.load_project(self.project_state.directory_path)
        ext = self.project_state.external
        self.external_edit.setText("" if ext is None else ext)
        self.settings_dialog.refresh_tabs_from_project()
