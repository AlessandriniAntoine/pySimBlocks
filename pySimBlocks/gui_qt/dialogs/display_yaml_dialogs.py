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

from pySimBlocks.gui_qt.model.project_state import ProjectState
from pySimBlocks.gui_qt.yaml_tools import dump_parameter_yaml, dump_model_yaml


class DisplayYamlDialog(QDialog):
    def __init__(self, project: ProjectState, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Generated YAML files")
        self.resize(900, 600)

        self.project_state = project

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
