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

        self.readonly = readonly
        if self.readonly:
            self.setWindowTitle(f"[{self.block.instance.name}] Information")
        else:
            self.setWindowTitle(f"Edit [{self.block.instance.name}] Parameters")
        self.setMinimumWidth(300)

        main_layout = QVBoxLayout(self)

        self.param_widgets: dict[str, QWidget] = {}
        self.param_labels: dict[str, QLabel] = {}
        self.depends_rules = {}

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
        meta_params = self.block.instance.meta.parameters
        inst_params = self.block.instance.parameters

        form = QFormLayout()
        self.description_part(form)

        # --- Block name ---
        self.name_edit = QLineEdit(self.block.instance.name)
        form.addRow(QLabel("Block name:"), self.name_edit)
        if self.readonly:
            self.name_edit.setReadOnly(True)

        for pname, pmeta in meta_params.items():
            widget = self._create_param_widget(pname, pmeta, inst_params)
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

            label = QLabel(f"{pname}:")
            if "description" in pmeta:
                label.setToolTip(pmeta["description"])
            form.addRow(label, widget)

            self.param_widgets[pname] = widget
            self.param_labels[pname] = label

            if "depends_on" in pmeta:
                self.depends_rules[pname] = pmeta["depends_on"]

        layout.addLayout(form)

        self.update_visibility()


    def update_visibility(self):
        inst_params = self.block.instance.parameters

        for pname, rules in self.depends_rules.items():
            visible = True

            dep_name = rules["parameter"]
            allowed_values = rules["values"]

            current_value = inst_params.get(dep_name)

            if current_value not in allowed_values:
                visible = False
                old_val = inst_params.get(pname)
                if old_val is not None:
                    self.block.instance.ui_cache[pname] = old_val
                inst_params[pname] = None  

            widget = self.param_widgets[pname]
            label = self.param_labels[pname]

            if visible:
                if inst_params.get(pname) is None:
                    if pname in self.block.instance.ui_cache:
                        restored = self.block.instance.ui_cache.pop(pname)
                        inst_params[pname] = restored
                        w = self.param_widgets[pname]
                        if isinstance(w, QLineEdit):
                            w.setText(str(restored))
                        elif isinstance(w, QComboBox):
                            w.setCurrentText(str(restored))

            widget.setVisible(visible)
            label.setVisible(visible)


    # ------------------------------------------------------------
    # Buttons
    # ------------------------------------------------------------
    def apply(self):
        if self.readonly:
            return
        
        def get_param_value(widget: 'QWidget'):
            if not widget.isVisible():
                return None

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

        if help_path.exists():
            dialog = HelpDialog(help_path, self)
            dialog.exec()
        else:
            QMessageBox.information(self, "Help", "No documentation available.")


    # ------------------------------------------------------------
    # internal methods
    def _create_param_widget(self, name, meta, inst_params):
        ptype = meta.get("type")
        value = inst_params.get(name)

        # ENUM
        if ptype == "enum":
            combo = QComboBox()
            for v in meta.get("enum", []):
                combo.addItem(str(v))
            if value is not None:
                combo.setCurrentText(str(value))
            combo.currentTextChanged.connect(
                lambda val, name=name: self._on_param_changed(name, val)
            )
            return combo

        # SCALAR / FLOAT / INT / VECTOR / MATRIX
        edit = QLineEdit()
        if value is not None:
            edit.setText(str(value))
        elif "default" in meta:
            edit.setText(str(meta["default"]))

        return edit


    def _on_param_changed(self, name, value):
        if self.readonly:
            return
        self.block.instance.parameters[name] = value
        self.update_visibility()
