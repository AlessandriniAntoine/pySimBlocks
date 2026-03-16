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

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QTabWidget,
    QTextEdit,
    QPushButton,
    QHBoxLayout,
)
from PySide6.QtGui import QFont

from pySimBlocks.gui.models.project_state import ProjectState
from pySimBlocks.gui.services.yaml_tools import dump_project_yaml
from pySimBlocks.gui.widgets.diagram_view import DiagramView


class DisplayYamlDialog(QDialog):
    """Preview the generated project YAML inside a dialog.

    Attributes:
        project_state: Project state being previewed.
        view: Diagram view supplying block layout information.
    """

    def __init__(self,
                 project: ProjectState,
                 view: DiagramView,
                 parent=None):
        """Initialize the YAML preview dialog.

        Args:
            project: Project state being previewed.
            view: Diagram view supplying block layout information.
            parent: Optional parent widget.

        Raises:
            None.
        """
        super().__init__(parent)

        self.setWindowTitle("project.yaml Preview")
        self.resize(900, 600)

        self.project_state = project
        self.view = view

        main_layout = QVBoxLayout(self)

        # -------------------------------------------------
        # Tabs
        # -------------------------------------------------
        tabs = QTabWidget()

        if self.view.block_items:
            blocks_items = self.view.block_items
        else:
            blocks_items = {}
        project_text = dump_project_yaml(self.project_state, blocks_items)
        tabs.addTab(
            self._make_code_view(project_text),
            "project.yaml"
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

    # --------------------------------------------------------------------------
    # Private Methods
    # --------------------------------------------------------------------------
    def _make_code_view(self, text:str) -> QTextEdit:
        """Build a read-only text editor configured for code display."""
        edit = QTextEdit()
        edit.setReadOnly(True)
        edit.setFont(QFont("Courier New", 10))
        edit.setPlainText(text)
        edit.setLineWrapMode(QTextEdit.NoWrap)
        return edit
