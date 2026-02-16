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

from abc import ABC
from pathlib import Path
from typing import Any, Dict, List, Literal

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QFrame,
    QLabel,
    QLineEdit,
    QSizePolicy,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from pySimBlocks.gui.blocks.parameter_meta import ParameterMeta
from pySimBlocks.gui.blocks.port_meta import PortMeta
from pySimBlocks.gui.model import BlockInstance, PortInstance


class BlockMeta(ABC):

    """
    Template for child class

from pySimBlocks.gui.blocks.block_meta import BlockMeta
from pySimBlocks.gui.blocks.parameter_meta import ParameterMeta
from pySimBlocks.gui.blocks.port_meta import PortMeta

class MyBlockMeta(BlockMeta):

    def __init__(self):
        self.name = ""
        self.category = ""
        self.type = ""
        self.summary = ""
        self.description = (
            ""
        )

        self.parameters = [
            ParameterMeta(
                name="",
                type=""
            ),
        ]

        self.inputs = [
            PortMeta(
                name="",
                display_as=""
                shape=...
            ),
        ]

        self.outputs = [
            PortMeta(
                name="",
                display_as=""
                shape=...
            ),
        ]
    """


    # ----------- Mandatory class attributes (must be overridden) -----------
    name: str
    category: str
    type: str
    summary: str
    description: str

    # ----------- Optional declarations -----------

    doc_path: Path | None = None
    parameters: List[ParameterMeta] = []
    inputs: List[PortMeta] = []
    outputs: List[PortMeta] = []

    param_widgets: Dict[str, QWidget] = {}
    param_labels: Dict[str, QLabel] = {}


    # --------------------------------------------------------------------------
    # Parameter resolution
    # --------------------------------------------------------------------------
    def get_param(self, param_name: str) -> ParameterMeta | None:
        for param in self.parameters:
            if param.name == param_name:
                return param
        return None

    def is_parameter_active(self, param_name: str, instance_values: Dict[str, Any]) -> bool:
        """
        Default: all parameters are always active.
        Children override if needed.
        """
        return True

    
    # --------------------------------------------------------------------------
    # Port resolution
    # --------------------------------------------------------------------------
    def resolve_port_group(self, 
                           port_meta: PortMeta,
                           direction: Literal['input', 'output'], 
                           instance: "BlockInstance"
    ) -> list["PortInstance"]:
        """
        Default behavior: fixed port.
        Children override for dynamic ports.
        """
        return [PortInstance(port_meta.name, port_meta.display_as, direction, instance)]
    
    # ------------------------------------------------------------
    def build_ports(self, instance: "BlockInstance") -> list["PortInstance"]:
        ports = []

        for pmeta in self.inputs:
            ports.extend(self.resolve_port_group(pmeta, "input", instance))

        for pmeta in self.outputs:
            ports.extend(self.resolve_port_group(pmeta, "output", instance))

        return ports


    # --------------------------------------------------------------------------
    # QT dialog display 
    # --------------------------------------------------------------------------
    def build_description(self, instance: BlockInstance, form: QFormLayout):
        """ Default description display. Children can override if needed. """
        title = QLabel(f"<b>{instance.meta.name}</b>")
        title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        form.addRow(title)

        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setFrameShadow(QFrame.Raised)
        frame.setLineWidth(1)

        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(8, 6, 8, 6)

        desc = QTextBrowser()
        desc.setMarkdown(instance.meta.description)
        desc.setReadOnly(True)
        desc.setFrameShape(QFrame.NoFrame)
        desc.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        desc.document().setTextWidth(400)
        desc.setFixedHeight(int(desc.document().size().height()) + 6)

        frame_layout.addWidget(desc)
        form.addRow(frame)


    # ------------------------------------------------------
    def build_pre_param(self, 
                        instance: BlockInstance,
                        form: QFormLayout, 
                        readonly: bool = False):
        """ Default: no pre-parameter widgets. Children override if needed. """
        pass

    # ------------------------------------------------------------
    def build_param(self, 
                    instance: BlockInstance,
                    form: QFormLayout, 
                    readonly: bool = False):
        """ Default: no parameter widgets. Children override if needed. """


        # --- Block name ---
        self.name_edit = QLineEdit(instance.name)
        form.addRow(QLabel("Block name:"), self.name_edit)
        if readonly:
            self.name_edit.setReadOnly(True)

        for param_meta in self.parameters:
            param_name = param_meta.name

            widget = self._create_param_widget(param_meta, 
                                               instance.parameters, readonly)
            if widget is None:
                continue
            if readonly:
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


    # ------------------------------------------------------------
    def build_post_param(self, 
                         instance: BlockInstance,
                         form: QFormLayout, 
                         readonly: bool = False):
        """ Default: no post-parameter widgets. Children override if needed. """
        pass

    # ------------------------------------------------------------
    def refresh_form(self, params: Dict[str, Any]):
        """
        Refresh the parameter widgets visibility based on
        BlockMeta.is_parameter_active and current local_params.
        """

        for param_name, widget in self.param_widgets.items():
            label = self.param_labels[param_name]

            active = self.is_parameter_active(param_name, params)

            widget.setVisible(active)
            label.setVisible(active)


    # --------------------------------------------------------------------------
    # Private methods
    # --------------------------------------------------------------------------
    def _create_param_widget(self, 
                             meta: ParameterMeta, 
                             inst_params: dict[str, Any],
                             readonly: bool = False
                             ) -> QWidget:
        # ENUM
        if meta.type == "enum":
            return self._create_enum_widget(meta, inst_params, readonly)
        
        # Default: text edit
        return self._create_edit_widget(meta, inst_params, readonly)


    # ------------------------------------------------------------
    def _create_edit_widget(self,
                            meta: ParameterMeta,
                            inst_params: dict[str, Any],
                            readonly: bool = False) -> QLineEdit:
        edit = QLineEdit()
        value = inst_params.get(meta.name)
        if value is not None:
            edit.setText(str(value))
        elif meta.default:
            edit.setText(str(meta.default))
        edit.textChanged.connect(
            lambda val: self._on_param_changed(val, meta.name, inst_params, readonly)
        )
        return edit

    # ------------------------------------------------------------
    def _create_enum_widget(self,
                            meta: ParameterMeta,
                            inst_params: dict[str, Any],
                            readonly: bool = False) -> QComboBox:
        combo = QComboBox()
        for v in meta.enum:
            combo.addItem(str(v))
        value = inst_params.get(meta.name)
        if value is not None:
            combo.setCurrentText(str(value))
        combo.currentTextChanged.connect(
            lambda val: self._on_param_changed(val, meta.name, inst_params, readonly)
        )
        return combo


    # ------------------------------------------------------------
    def _on_param_changed(self, value, name, params, readonly):
        if readonly:
            return
        params[name] = value
        self.refresh_form(params)
