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

from pathlib import Path
import os
from PySide6.QtWidgets import (
    QWidget, QFormLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QFileDialog, QHBoxLayout
)

from pySimBlocks.gui.model.project_state import ProjectState
from pySimBlocks.gui.project_controller import ProjectController
from pySimBlocks.gui.services.project_loader import ProjectLoaderYaml


class ProjectSettingsWidget(QWidget):

    def __init__(self, project_state: ProjectState, project_controller: ProjectController, settings_dialg):
        super().__init__()
        self.project_state = project_state
        self.project_controller = project_controller
        self.settings_dialog = settings_dialg

        layout = QFormLayout(self)
        layout.addRow(QLabel("<b>Project Settings</b>"))

        self.dir_edit = QLineEdit(str(project_state.directory_path))
        self.dir_browse_btn = QPushButton("...")
        self.dir_browse_btn.setToolTip("Select a project directory from disk")
        self.dir_browse_btn.clicked.connect(self.browse_project_directory)

        dir_layout = QHBoxLayout()
        dir_layout.setContentsMargins(0, 0, 0, 0)
        dir_layout.addWidget(self.dir_edit)
        dir_layout.addWidget(self.dir_browse_btn)

        layout.addRow("Directory path:", dir_layout)

        load_btn = QPushButton("Load")
        load_btn.clicked.connect(self.load_project)
        label = QLabel("Load Project:")
        label.setToolTip("Auto Load project from directory with parameters and model yaml.")
        layout.addRow(label, load_btn)

        ext = project_state.external or ""
        self.external_edit = QLineEdit(ext)
        self.external_browse_btn = QPushButton("...")
        self.external_browse_btn.setToolTip("Select a Python file from disk")
        self.external_browse_btn.clicked.connect(self.browse_external_file)

        external_layout = QHBoxLayout()
        external_layout.setContentsMargins(0, 0, 0, 0)
        external_layout.addWidget(self.external_edit)
        external_layout.addWidget(self.external_browse_btn)

        label = QLabel("Python file:")
        label.setToolTip("Relative path from project directory")
        layout.addRow(label, external_layout)



    def apply(self) -> bool:
        path = Path(self.dir_edit.text())
        if not path.exists():
            QMessageBox.warning(
                self,
                "Invalid directory",
                f"The directory does not exist:\n{path}",
            )
            return False
        ext = self.external_edit.text().strip()
        self.project_controller.update_project_param(path, ext)
        return True

    def browse_external_file(self):
        base_dir = Path(self.dir_edit.text()).expanduser()
        if not base_dir.is_dir():
            QMessageBox.warning(
                self,
                "Invalid directory",
                f"The directory does not exist:\n{base_dir}",
            )
            return

        selected_file, _ = QFileDialog.getOpenFileName(
            self,
            "Select Python file",
            str(base_dir),
            "Python files (*.py);;All files (*)",
        )

        if not selected_file:
            return

        selected_path = Path(selected_file).resolve()
        try:
            relative_path = selected_path.relative_to(base_dir.resolve())
        except ValueError:
            relative_path = Path(os.path.relpath(str(selected_path), str(base_dir.resolve())))

        self.external_edit.setText(str(relative_path))

    def browse_project_directory(self):
        current_dir = Path(self.dir_edit.text()).expanduser()
        start_dir = current_dir if current_dir.is_dir() else Path.cwd()

        selected_dir = QFileDialog.getExistingDirectory(
            self,
            "Select project directory",
            str(start_dir),
        )

        if not selected_dir:
            return

        self.dir_edit.setText(str(Path(selected_dir).resolve()))

    def load_project(self):
        self.apply()
        self.project_controller.load_project(ProjectLoaderYaml())
        ext = self.project_state.external
        self.external_edit.setText("" if ext is None else ext)
        self.settings_dialog.refresh_tabs_from_project()
