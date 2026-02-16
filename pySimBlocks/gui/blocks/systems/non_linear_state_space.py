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

from pySimBlocks.gui.blocks.block_meta import BlockMeta, ParameterMeta
from pySimBlocks.gui.blocks.port_meta import PortMeta
from pySimBlocks.gui.models import BlockInstance, PortInstance


class NonLinearStateSpaceMeta(BlockMeta):

    def __init__(self):
        self.name = "Non Linear State Space"
        self.category = "systems"
        self.type = "non_linear_state_space"
        self.summary = "User-defined non linear state space function implemented in Python."
        self.description = (
            "This block evaluates a user-provided Python function of the form:\n"
            "    x+ = f(t, dt, x, u1, u2, ...)\n"
            "    y = g(t, dt, x)\n"
            "The function is loaded from an external Python file and executed at each\n"
            "simulation step. Input and output ports are explicitly declared via\n"
            "`input_keys` and `output_keys`.\n"
        )

        self.parameters = [
            ParameterMeta(
                name="file_path",
                type="string",
                required=True,
                description="Path to the Python file containing the functions relative to the parameters.yaml file."
            ),
            ParameterMeta(
                name="state_function_name",
                type="string",
                required=True,
                description="Name of the state function to call inside the Python file."
            ),
            ParameterMeta(
                name="output_function_name",
                type="string",
                required=True,
                description="Name of the output function to call inside the Python file."
            ),
            ParameterMeta(
                name="input_keys",
                type="list[string]",
                required=True,
                description="List of input port names. These must match the function arguments after (t, dt)."
            ),
            ParameterMeta(
                name="output_keys",
                type="list[string]",
                required=True,
                description="List of output port names. The function must return a dict with exactly these keys."
            ),
            ParameterMeta(
                name="x0",
                type="vector",
                required=True,
                description="Initial state vector."
            ),
            ParameterMeta(
                name="sample_time",
                type="float",
                description="Optional execution period of the block."
            )
        ]

        self.inputs = [
            PortMeta(
                name="in",
                display_as="",
                shape=[]  # shapes are dynamic
            )
        ]

        self.outputs = [
            PortMeta(
                name="out",
                display_as="",
                shape=[]  # shapes are dynamic
            )
        ]

    # --------------------------------------------------------------------------
    # Port resolution
    # --------------------------------------------------------------------------
    def resolve_port_group(
        self,
        port_meta: PortMeta,
        direction: Literal['input', 'output'],
        instance: "BlockInstance"
    ) -> list["PortInstance"]:
        if direction == 'input' and port_meta.name == 'in':
            input_keys = instance.parameters.get("input_keys", [])
            if input_keys is None:
                return []
            return [
                PortInstance(
                    name=key,
                    display_as=key,
                    direction="input",
                    block=instance
                ) for key in input_keys
            ]
        elif direction == 'output' and port_meta.name == 'out':
            output_keys = instance.parameters.get("output_keys", [])
            if output_keys is None:
                return []
            return [
                PortInstance(
                    name=key,
                    display_as=key,
                    direction="output",
                    block=instance
                ) for key in output_keys
            ]
        return super().resolve_port_group(port_meta, direction, instance)

    # --------------------------------------------------------------------------
    # Dialog methods
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
            if pmeta.name == "file_path":
                self.build_file_param_row(
                    session,
                    form,
                    pmeta,
                    readonly=readonly,
                    file_filter="Python files (*.py);;All files (*)",
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
        raw = session.local_params.get("file_path")
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
            btn.setToolTip("Set a valid existing file_path to open the file.")

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
