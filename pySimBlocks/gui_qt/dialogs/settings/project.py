from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QFormLayout, QLabel, QLineEdit, QMessageBox
)

from pySimBlocks.gui_qt.model.project_state import ProjectState


class ProjectSettingsWidget(QWidget):
    def __init__(self, project: ProjectState):
        super().__init__()
        self.project = project

        layout = QFormLayout(self)
        layout.addRow(QLabel("<b>Project Settings</b>"))

        self.dir_edit = QLineEdit(str(project.directory_path))
        layout.addRow("Directory path:", self.dir_edit)

        ext = project.external or ""
        self.external_edit = QLineEdit(ext)
        label = QLabel("Python file:")
        label.setToolTip("Relative path from project directory")
        layout.addRow(label, self.external_edit)

    def apply(self) -> bool:
        path = Path(self.dir_edit.text())
        if not path.exists():
            QMessageBox.warning(
                self,
                "Invalid directory",
                f"The directory does not exist:\n{path}",
            )
            return False

        self.project.directory_path = path
        ext = self.external_edit.text().strip()
        self.project.external = None if ext == "" else ext
        return True
