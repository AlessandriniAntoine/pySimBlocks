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

import os
import subprocess
import sys
from pathlib import Path
from typing import Literal

from PySide6.QtWidgets import QFormLayout, QLabel, QLineEdit, QPushButton

from pySimBlocks.gui.blocks.block_meta import BlockMeta
from pySimBlocks.gui.blocks.parameter_meta import ParameterMeta
from pySimBlocks.gui.blocks.port_meta import PortMeta
from pySimBlocks.gui.models import BlockInstance, PortInstance


class SofaExchangeIOMeta(BlockMeta):

    def __init__(self):
        self.name = "SofaExchangeIO"
        self.category = "systems"
        self.type = "sofa_exchange_i_o"
        self.summary = "Interface block for exchanging signals between pySimBlocks and SOFA."
        self.description = (
            "Provides a stateless interface block that exposes dynamic input and output\n"
            "ports to connect a pySimBlocks model with an external SOFA controller.\n"
            "This block does not execute a SOFA simulation."
        )

        self.parameters = [
            ParameterMeta(
                name="scene_file",
                type="string",
                description="Path to the SOFA scene file used for automatic generation relative to parameters.yaml file."
            ),
            ParameterMeta(
                name="input_keys",
                type="list[string]",
                required=True,
                description="List of input keys corresponding to SOFA input ports."
            ),
            ParameterMeta(
                name="output_keys",
                type="list[string]",
                required=True,
                description="List of output keys corresponding to SOFA output ports."
            ),
            ParameterMeta(
                name="slider_params",
                type="dict",
                description="Dictionary of slider parameters to be modified in the SOFA scene at runtime."
            ),
            ParameterMeta(
                name="sample_time",
                type="float"
            )
        ]

        self.inputs = [
            PortMeta(
                name="sofa_inputs",
                display_as="",
                shape=[]
            )
        ]

        self.outputs = [
            PortMeta(
                name="sofa_outputs",
                display_as="",
                shape=[]
            )
        ]

    # --------------------------------------------------------------------------
    # Port Resolution
    # --------------------------------------------------------------------------
    def resolve_port_group(
        self,
        port_meta: PortMeta,
        direction: Literal["input", "output"],
        instance: "BlockInstance"
    ) -> list["PortInstance"]:

        if direction == "input" and port_meta.name == "sofa_inputs":
            keys = instance.parameters.get("input_keys", [])
            if keys is None:
                return []
            return [
                PortInstance(
                    name=key,
                    display_as=key,
                    direction="input",
                    block=instance
                )
                for key in keys
            ]

        if direction == "output" and port_meta.name == "sofa_outputs":
            keys = instance.parameters.get("output_keys", [])
            if keys is None:
                return []
            return [
                PortInstance(
                    name=key,
                    display_as=key,
                    direction="output",
                    block=instance
                )
                for key in keys
            ]

        return super().resolve_port_group(port_meta, direction, instance)

    # --------------------------------------------------------------------------
    # Dialog Methods
    # --------------------------------------------------------------------------
    def build_param(
        self,
        session,
        form: QFormLayout,
        readonly: bool = False,
    ):
        name_edit = QLineEdit(session.instance.name)
        name_edit.textChanged.connect(
            lambda val: self._on_param_changed(val, "name", session, readonly)
        )
        form.addRow(QLabel("Block name:"), name_edit)
        if readonly:
            name_edit.setReadOnly(True)
        session.name_edit = name_edit

        for pmeta in self.parameters:
            if pmeta.name == "scene_file":
                self.build_file_param_row(
                    session,
                    form,
                    pmeta,
                    readonly=readonly,
                    file_filter="SOFA scene files (*.py);;All files (*)",
                )
                continue

            label, widget = self._create_param_row(session, pmeta, readonly)
            if widget is None:
                continue
            if readonly:
                self._set_readonly_style(widget)

            form.addRow(label, widget)
            session.param_widgets[pmeta.name] = widget
            session.param_labels[pmeta.name] = label

    # ------------------------------------------------------
    def build_post_param(self, session, form: QFormLayout, readonly: bool = False):
        open_btn = QPushButton("Open file")
        open_btn.clicked.connect(lambda: self._open_file_from_session(session))
        form.addRow(QLabel(""), open_btn)
        session.open_file_btn = open_btn
        self._refresh_open_button_state(session)

    # ------------------------------------------------------
    def refresh_form(self, session):
        super().refresh_form(session)
        self._refresh_open_button_state(session)

    # ------------------------------------------------------
    def _resolve_file_path(self, session) -> Path | None:
        raw = session.local_params.get("scene_file")
        if not raw:
            return None

        path = Path(str(raw)).expanduser()
        if not path.is_absolute() and session.project_dir is not None:
            path = (session.project_dir / path).resolve()
        return path

    # ------------------------------------------------------
    def _refresh_open_button_state(self, session) -> None:
        btn = getattr(session, "open_file_btn", None)
        if btn is None:
            return

        target = self._resolve_file_path(session)
        exists = target is not None and target.is_file()
        btn.setEnabled(exists)
        if exists:
            btn.setToolTip(str(target))
        else:
            btn.setToolTip("Set a valid existing scene_file to open the file.")

    # ------------------------------------------------------
    def _open_file_from_session(self, session) -> None:
        target = self._resolve_file_path(session)
        if target is None or not target.is_file():
            return

        if sys.platform.startswith("darwin"):
            subprocess.Popen(["open", str(target)])
        elif os.name == "nt":
            os.startfile(str(target))
        else:
            subprocess.Popen(["xdg-open", str(target)])
