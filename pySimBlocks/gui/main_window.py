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

from pathlib import Path
from typing import List

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QMainWindow, QSplitter

from pySimBlocks.gui.blocks.block_meta import BlockMeta
from pySimBlocks.gui.dialogs.unsaved_dialog import UnsavedChangesDialog
from pySimBlocks.gui.models.project_state import ProjectState
from pySimBlocks.gui.project_controller import ProjectController
from pySimBlocks.gui.services.project_loader import ProjectLoaderYaml
from pySimBlocks.gui.services.project_saver import ProjectSaverYaml
from pySimBlocks.gui.services.simulation_runner import SimulationRunner
from pySimBlocks.gui.services.yaml_tools import cleanup_runtime_project_yaml
from pySimBlocks.gui.widgets.block_list import BlockList
from pySimBlocks.gui.widgets.diagram_view import DiagramView
from pySimBlocks.gui.widgets.toolbar_view import ToolBarView
from pySimBlocks.tools.blocks_registry import load_block_registry


class MainWindow(QMainWindow):
    """Main application window for the pySimBlocks GUI editor.

    Assembles the block library panel, diagram canvas, and toolbar. Manages
    project load/save/run operations and tracks unsaved changes.

    Attributes:
        loader: Service used to load a project from YAML.
        saver: Service used to save a project to YAML.
        runner: Service used to launch a simulation.
        block_registry: Registry mapping category → block type → BlockMeta.
        project_state: Shared mutable state of the currently open project.
        view: The diagram canvas widget.
        project_controller: Controller coordinating model and view mutations.
        blocks: Block-library side panel widget.
        toolbar: Toolbar widget with run/save actions.
    """

    def __init__(self, project_path: Path):
        """Initialize the MainWindow and open the project at ``project_path``.

        Args:
            project_path: Path to the project directory. If a ``project.yaml``
                file is found inside it, the project is loaded automatically.
        """
        super().__init__()

        self.loader = ProjectLoaderYaml()
        self.saver = ProjectSaverYaml()
        self.runner = SimulationRunner()

        self.block_registry = load_block_registry()

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
        self.quit_action.setShortcut(QKeySequence("Ctrl+Q"))
        self.quit_action.triggered.connect(self.close)
        self.addAction(self.quit_action)

        QTimer.singleShot(0, self.view.setFocus)


    # --------------------------------------------------------------------------
    # Registry
    # --------------------------------------------------------------------------

    def get_categories(self) -> List[str]:
        """Return the sorted list of block categories from the registry.

        Returns:
            Sorted list of category name strings.
        """
        return sorted(self.block_registry.keys())

    def get_blocks(self, category: str) -> List[str]:
        """Return the sorted list of block type names within a category.

        Args:
            category: Category name to look up.

        Returns:
            Sorted list of block type name strings.
        """
        return sorted(self.block_registry.get(category, {}).keys())

    def resolve_block_meta(self, category: str, block_type: str) -> BlockMeta:
        """Return the :class:`BlockMeta` for a given category and block type.

        Args:
            category: Category name of the block.
            block_type: Type name of the block within the category.

        Returns:
            The :class:`BlockMeta` descriptor for the requested block.
        """
        return self.block_registry[category][block_type]


    # --------------------------------------------------------------------------
    # Auto load
    # --------------------------------------------------------------------------

    def auto_load_detection(self, project_path: Path) -> bool:
        """Return True if a recognisable project file is found in ``project_path``.

        Args:
            project_path: Directory to search for a project file.

        Returns:
            True if ``project.yaml`` exists in the directory, False otherwise.
        """
        project_yaml = self._auto_detect_yaml(project_path, ["project.yaml"])
        return project_yaml is not None

    def _auto_detect_yaml(self, project_path: Path, names: list[str]) -> str | None:
        """Return the path of the first matching file in the project directory."""
        for name in names:
            path = project_path / name
            if path.is_file():
                return str(path)
        return None


    # --------------------------------------------------------------------------
    # Project management
    # --------------------------------------------------------------------------

    def update_window_title(self) -> None:
        """Refresh the window title to reflect the project name and dirty state."""
        path = self.project_state.directory_path
        project_name = path.name if path else "Untitled"
        star = "*" if self.project_controller.is_dirty else ""
        self.setWindowTitle(f"{project_name}{star} – pySimBlocks")

    def on_project_loaded(self, project_path: Path) -> None:
        """Refresh the window title after a project has been loaded.

        Args:
            project_path: Path to the newly loaded project directory.
        """
        self.update_window_title()

    def cleanup(self) -> None:
        """Remove any runtime-generated project YAML files on exit."""
        cleanup_runtime_project_yaml(self.project_state.directory_path)

    def closeEvent(self, event) -> None:
        """Intercept the close event to prompt the user about unsaved changes.

        Args:
            event: Qt close event.
        """
        if self.confirm_discard_or_save("closing"):
            self.cleanup()
            event.accept()
        else:
            event.ignore()

    def confirm_discard_or_save(self, action_name: str) -> bool:
        """Show an unsaved-changes dialog if the project is dirty.

        Args:
            action_name: Human-readable name of the triggering action (e.g.
                ``'closing'``), displayed in the dialog message.

        Returns:
            True if the action should proceed (user saved or discarded
            changes), False if the user cancelled.
        """
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

    def _on_save(self) -> None:
        """Save the project if there are unsaved changes."""
        if not self.project_controller.is_dirty:
            return
        self.saver.save(self.project_controller.project_state, self.project_controller.view.block_items)
        self.project_controller.clear_dirty()
