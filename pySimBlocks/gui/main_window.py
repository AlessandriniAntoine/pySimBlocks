# ******************************************************************************
#                                  pySimBlocks
#                     Copyright (c) 2026 Antoine Alessandrini
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

import shutil
from pathlib import Path
from typing import Dict, List

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QMainWindow, QSplitter

from pySimBlocks.gui.dialogs.unsaved_dialog import UnsavedChangesDialog
from pySimBlocks.gui.model.project_state import ProjectState
from pySimBlocks.gui.project_controller import ProjectController
from pySimBlocks.gui.services.project_loader import ProjectLoaderYaml
from pySimBlocks.gui.services.project_saver import ProjectSaverYaml
from pySimBlocks.gui.services.simulation_runner import SimulationRunner
from pySimBlocks.gui.widgets.block_list import BlockList
from pySimBlocks.gui.widgets.diagram_view import DiagramView
from pySimBlocks.gui.widgets.toolbar_view import ToolBarView
from pySimBlocks.tools.blocks_registry import (
    BlockMeta,
    BlockRegistry,
    load_block_registry,
)

registry: BlockRegistry = load_block_registry()


class MainWindow(QMainWindow):
    def __init__(self, project_path: Path):
        super().__init__()

        self.loader = ProjectLoaderYaml()
        self.saver = ProjectSaverYaml()
        self.runner = SimulationRunner()

        self.loader = ProjectLoaderYaml()
        self.saver = ProjectSaverYaml()
        self.runner = SimulationRunner()

        self.project_state = ProjectState(project_path)
        self.view = DiagramView()
        self.project_controller = ProjectController(self.project_state, self.view, self.resolve_block_meta)
        self.view.project_controller = self.project_controller
        self.blocks = BlockList(self.get_categories, self.get_blocks, self.resolve_block_meta)
        self.toolbar = ToolBarView(self.saver, self.runner, self.project_controller)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.blocks)
        splitter.addWidget(self.view)
        splitter.setSizes([180, 800])
        
        self.setCentralWidget(splitter)
        self.addToolBar(self.toolbar)

        flag = self.auto_load_detection(project_path)
        if flag:
            self.project_controller.load_project(self.loader)

        self.project_controller.dirty_changed.connect(self.update_window_title)
        self.update_window_title()

        self.save_action = QAction("Save", self)
        self.save_action.setShortcut(QKeySequence.Save)
        self.save_action.triggered.connect(self._on_save)
        self.addAction(self.save_action)

        self.quit_action = QAction("Quit", self)
        self.quit_action.setShortcut(QKeySequence.Quit)
        self.quit_action.triggered.connect(self.close)
        self.addAction(self.quit_action)

    # --------------------------------------------------------------------------
    # Registry
    # --------------------------------------------------------------------------
    def get_categories(self) -> List[str]:
        return sorted(registry.keys())

    # ------------------------------------------------------------------
    def get_blocks(self, category: str) -> List[str]:
        return sorted(registry[category].keys()) 

    # ------------------------------------------------------------------
    def resolve_category_meta(self, category: str) -> Dict[str, BlockMeta]:
        return registry[category]

    # ------------------------------------------------------------------
    def resolve_block_meta(self, category: str, block_type: str) -> BlockMeta:
        return registry[category][block_type]


    # --------------------------------------------------------------------------
    # Auto Load 
    # --------------------------------------------------------------------------
    def auto_load_detection(self, project_path: Path) -> bool:
        param_yaml = self._auto_detect_yaml(
            project_path, ["parameters.yaml"])
        model_yaml = self._auto_detect_yaml(
            project_path, ["model.yaml"])
        if param_yaml and model_yaml:
            return True
        return False

    # ------------------------------------------------------------------
    def _auto_detect_yaml(self, project_path: Path, names: list[str]) -> str | None:
        for name in names:
            path = project_path / name
            if path.is_file():
                return str(path)
        return None

    # --------------------------------------------------------------------------
    # Project Management
    # --------------------------------------------------------------------------
    def _on_save(self):
        if not self.project_controller.is_dirty:
            return
        self.saver.save(self.project_controller.project_state, self.project_controller.view.block_items)
        self.project_controller.clear_dirty()

    # ------------------------------------------------------------------
    def update_window_title(self):
        path = self.project_state.directory_path
        project_name = path.name if path else "Untitled"
        star = "*" if self.project_controller.is_dirty else ""
        self.setWindowTitle(f"{project_name}{star} – pySimBlocks")

    # ------------------------------------------------------------------
    def on_project_loaded(self, project_path: Path):
        self.update_window_title()

    # ------------------------------------------------------------------
    def cleanup(self):
        temp_path = self.project_state.directory_path / ".temp"
        if temp_path.exists():
            shutil.rmtree(temp_path, ignore_errors=True)

    # ------------------------------------------------------------------
    def closeEvent(self, event):
        if self._confirm_discard_or_save("closing"):
            self.cleanup()
            event.accept()
        else:
            event.ignore() 

    # ------------------------------------------------------------------
    def _confirm_discard_or_save(self, action_name: str) -> bool:
        if not self.project_controller.is_dirty:
            return True

        dlg = UnsavedChangesDialog(action_name, self)
        result = dlg.exec()

        if result == UnsavedChangesDialog.SAVE:
            self._on_save()
            return True
        elif result == UnsavedChangesDialog.DISCARD:
            return True
        else:
            return False
