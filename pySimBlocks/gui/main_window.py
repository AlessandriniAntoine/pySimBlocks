from pathlib import Path
import shutil
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
)

from pySimBlocks.gui.services.project_controller import ProjectController
from pySimBlocks.tools.blocks_registry import load_block_registry
from pySimBlocks.gui.widgets.block_list import BlockList
from pySimBlocks.gui.widgets.diagram_view import DiagramView
from pySimBlocks.gui.widgets.toolbar_view import ToolBarView
from pySimBlocks.gui.model.project_state import ProjectState


registry = load_block_registry()
categories = sorted(registry.keys())

class MainWindow(QMainWindow):
    def __init__(self, project_path: Path):
        super().__init__()
        self.setWindowTitle("pySimBlocks — Qt Edition")

        central = QWidget()
        layout = QHBoxLayout(central)

        self.project_state = ProjectState(project_path)
        self.diagram = DiagramView(self.resolve_block_meta, self.project_state)
        self.project_controller = ProjectController(self.project_state, self.diagram, self.resolve_block_meta)
        self.blocks = BlockList(self.get_categories, self.get_blocks, self.resolve_block_meta)
        self.toolbar = ToolBarView(self.project_state, self.project_controller)

        self.blocks.setFixedWidth(220)

        layout.addWidget(self.blocks)
        layout.addWidget(self.diagram)
        self.addToolBar(self.toolbar)
        self.setCentralWidget(central)
        flag = self.auto_load_detection(project_path)
        if flag:
            self.project_controller.load_project(project_path)

    def cleanup(self):
        temp_path = self.project_state.directory_path / ".temp"
        if temp_path.exists():
            shutil.rmtree(temp_path, ignore_errors=True)


    ####################### Registry ########################
    def get_categories(self):
        return categories.copy()

    def get_blocks(self, category):
        return sorted(registry[category].keys())

    def resolve_category_meta(self, category):
        return registry[category]

    def resolve_block_meta(self, category, block_type):
        return registry[category][block_type]


    ####################### Auto Load ########################
    def auto_load_detection(self, project_path: Path):
        param_yaml = self._auto_detect_yaml(
            project_path, ["parameters.yaml"])
        model_yaml = self._auto_detect_yaml(
            project_path, ["model.yaml"])
        if param_yaml and model_yaml:
            return True

    def _auto_detect_yaml(self, project_path: Path, names: list[str]) -> str | None:
        for name in names:
            path = project_path / name
            if path.is_file():
                return str(path)
        return None
