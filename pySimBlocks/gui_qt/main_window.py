import os
import sys
from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
)

from pySimBlocks.tools.blocks_registry import load_block_registry
from pySimBlocks.gui_qt.widgets.block_list import BlockList
from pySimBlocks.gui_qt.widgets.diagram_view import DiagramView
from pySimBlocks.gui_qt.widgets.toolbar_view import ToolBarView
from pySimBlocks.gui_qt.model.project_state import ProjectState



registry = load_block_registry()
categories = sorted(registry.keys())
# --------------------------------------------------
# Project directory from CLI
# --------------------------------------------------
if len(sys.argv) > 1:
    project_dir = os.path.abspath(sys.argv[1])
else:
    project_dir = os.getcwd()
project_path = Path(project_dir).resolve()



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("pySimBlocks — Qt prototype")

        central = QWidget()
        layout = QHBoxLayout(central)
        self.project = ProjectState(project_path)

        self.blocks = BlockList(self.get_categories, self.get_blocks)
        self.diagram = DiagramView(self.resolve_block_meta, self.project)
        self.toolbar = ToolBarView(self.project)

        self.blocks.setFixedWidth(220)

        layout.addWidget(self.blocks)
        layout.addWidget(self.diagram)


        self.simulation_config = {
            "dt": 0.01,
            "solver": "fixed",
            "external_file": "",
        }

        self.addToolBar(self.toolbar)



        self.setCentralWidget(central)





    ####################### Registry ########################
    def get_categories(self):
        return categories.copy()

    def get_blocks(self, category):
        return sorted(registry[category].keys())

    def resolve_category_meta(self, category):
        return registry[category]

    def resolve_block_meta(self, category, block_type):
        return registry[category][block_type]
