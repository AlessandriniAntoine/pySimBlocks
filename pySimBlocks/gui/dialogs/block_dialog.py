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

import ast

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTextBrowser,
    QVBoxLayout,
)

from pySimBlocks.gui.blocks.block_meta import ParameterMeta
from pySimBlocks.gui.dialogs.help_dialog import HelpDialog

from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from pySimBlocks.gui.graphics.block_item import BlockItem
    from PySide6.QtWidgets import QWidget


class BlockDialog(QDialog):
    def __init__(self,
                 block: 'BlockItem',
                 readonly: bool = False
    ):
        super().__init__()
        self.block = block
        self.local_params: dict[str, Any] = dict(block.instance.parameters)

        self.readonly = readonly
        if self.readonly:
            self.setWindowTitle(f"[{self.block.instance.name}] Information")
        else:
            self.setWindowTitle(f"Edit [{self.block.instance.name}] Parameters")
        self.setMinimumWidth(300)

        self.param_widgets: dict[str, QWidget] = {}
        self.param_labels: dict[str, QLabel] = {}

        main_layout = QVBoxLayout(self)
        self.build_parameters_form(main_layout)

        # --- Buttons row ---
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        ok_btn = QPushButton("Ok")
        ok_btn.setDefault(True)
        ok_btn.setAutoDefault(True)
        ok_btn.clicked.connect(self.ok)
        buttons_layout.addWidget(ok_btn)

        help_btn = QPushButton("Help")
        help_btn.clicked.connect(self.open_help)
        buttons_layout.addWidget(help_btn)

        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self.apply)
        buttons_layout.addWidget(apply_btn)

        main_layout.addLayout(buttons_layout)

    # ------------------------------------------------------------
    # Form
    def description_part(self, form):
        title = QLabel(f"<b>{self.block.instance.meta.name}</b>")
        title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        form.addRow(title)

        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setFrameShadow(QFrame.Raised)
        frame.setLineWidth(1)

        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(8, 6, 8, 6)

        desc = QTextBrowser()
        desc.setMarkdown(self.block.instance.meta.description)
        desc.setReadOnly(True)
        desc.setFrameShape(QFrame.NoFrame)
        desc.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        desc.document().setTextWidth(400)
        desc.setFixedHeight(int(desc.document().size().height()) + 6)

        frame_layout.addWidget(desc)
        form.addRow(frame)

    def build_parameters_form(self, layout):
        meta = self.block.instance.meta
        inst_params = self.block.instance.parameters

        form = QFormLayout()
        self.description_part(form)

        # --- Block name ---
        self.name_edit = QLineEdit(self.block.instance.name)
        form.addRow(QLabel("Block name:"), self.name_edit)
        if self.readonly:
            self.name_edit.setReadOnly(True)

        for param_meta in meta.parameters:
            param_name = param_meta.name

            widget = self._create_param_widget(param_meta, inst_params)
            if widget is None:
                continue
            if self.readonly:
                if isinstance(widget, QLineEdit):
                    widget.setReadOnly(True)
                    widget.setStyleSheet("""
                        QLineEdit {
                            background-color: #2b2b2b;
                            color: #888888;
                            border: 1px solid #444444;
                        }
                    """)
                elif isinstance(widget, QComboBox):
                    widget.setEnabled(False)

            label = QLabel(f"{param_name}:")
            if param_meta.description:
                label.setToolTip(param_meta.description)
            form.addRow(label, widget)

            self.param_widgets[param_name] = widget
            self.param_labels[param_name] = label

        layout.addLayout(form)
        self.refresh_form()

    def refresh_form(self):
        """
        Refresh the parameter widgets visibility based on
        BlockMeta.is_parameter_active and current local_params.
        """
        meta = self.block.instance.meta

        for param_name, widget in self.param_widgets.items():
            label = self.param_labels[param_name]

            active = meta.is_parameter_active(param_name, self.local_params)

            widget.setVisible(active)
            label.setVisible(active)
    
    # ------------------------------------------------------------
    # Buttons
    # ------------------------------------------------------------
    def apply(self):
        if self.readonly:
            return

        def get_param_value(widget: 'QWidget'):
            if isinstance(widget, QComboBox):
                return widget.currentText()

            if isinstance(widget, QLineEdit):
                text = widget.text().strip()
                if not text:
                    return None
                try:
                    return ast.literal_eval(text)
                except Exception:
                    return text

            return None

        params: dict[str, Any] = {
            "name": self.name_edit.text(),
            **{
                pname: get_param_value(widget)
                for pname, widget in self.param_widgets.items()
            }
        }

        self.block.view.update_block_param_event(self.block.instance, params)

    def ok(self):
        self.apply()
        self.accept()


    def open_help(self):
        help_path = self.block.instance.meta.doc_path

        if help_path and help_path.exists():
            HelpDialog(help_path, self).exec()
        else:
            QMessageBox.information(self, "Help", "No documentation available.")


    # ------------------------------------------------------------
    # internal methods
    def _create_param_widget(self, 
                             meta: ParameterMeta, 
                             inst_params: dict[str, Any]
    ):
        param_name = meta.name
        param_type = meta.type
        value = inst_params.get(param_name)

        # ENUM
        if param_type == "enum":
            combo = QComboBox()
            for v in meta.enum:
                combo.addItem(str(v))
            if value is not None:
                combo.setCurrentText(str(value))
            combo.currentTextChanged.connect(
                lambda val, name=param_name: self._on_param_changed(name, val)
            )
            return combo

        # SCALAR / FLOAT / INT / VECTOR / MATRIX
        edit = QLineEdit()
        if value is not None:
            edit.setText(str(value))
        elif meta.default:
            edit.setText(str(meta.default))

        return edit


    def _on_param_changed(self, name, value):
        if self.readonly:
            return
        self.local_params[name] = value
        self.refresh_form()
