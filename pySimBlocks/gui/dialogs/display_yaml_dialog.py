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

import yaml

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QTabWidget,
    QTextEdit,
    QPushButton,
    QHBoxLayout,
)
from PySide6.QtGui import QFont

from pySimBlocks.gui.model.project_state import ProjectState
from pySimBlocks.gui.services.yaml_tools import dump_parameter_yaml, dump_model_yaml, dump_layout_yaml
from pySimBlocks.gui.widgets.diagram_view import DiagramView


class DisplayYamlDialog(QDialog):
    def __init__(self,
                 project: ProjectState,
                 view: DiagramView,
                 parent=None):
        super().__init__(parent)

        self.setWindowTitle("Generated YAML files")
        self.resize(900, 600)

        self.project_state = project
        self.view = view

        main_layout = QVBoxLayout(self)

        # -------------------------------------------------
        # Tabs
        # -------------------------------------------------
        tabs = QTabWidget()

        # Parameters.yaml
        ptext = dump_parameter_yaml(self.project_state)
        tabs.addTab(
            self._make_code_view(ptext),
            "parameters.yaml"
        )

        # Model.yaml
        mtext = dump_model_yaml(self.project_state)
        tabs.addTab(
            self._make_code_view(mtext),
            "model.yaml"
        )

        # Layout.yaml
        if self.view.block_items:
            blocks_items = self.view.block_items
        else:
            blocks_items = {}
        ltext = dump_layout_yaml(blocks_items)
        tabs.addTab(
            self._make_code_view(ltext),
            "layout.yaml"
        )

        main_layout.addWidget(tabs)

        # -------------------------------------------------
        # Buttons
        # -------------------------------------------------
        buttons = QHBoxLayout()
        buttons.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        buttons.addWidget(close_btn)

        main_layout.addLayout(buttons)

    # -------------------------------------------------
    # Helpers
    # -------------------------------------------------
    def _make_code_view(self, text:str) -> QTextEdit:
        edit = QTextEdit()
        edit.setReadOnly(True)
        edit.setFont(QFont("Courier New", 10))
        edit.setPlainText(text)
        edit.setLineWrapMode(QTextEdit.NoWrap)
        return edit
