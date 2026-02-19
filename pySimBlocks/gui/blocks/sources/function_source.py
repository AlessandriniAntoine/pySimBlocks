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

from PySide6.QtWidgets import QFormLayout, QLabel, QLineEdit, QPushButton

from pySimBlocks.gui.blocks.block_meta import BlockMeta, ParameterMeta
from pySimBlocks.gui.blocks.port_meta import PortMeta


class FunctionSourceMeta(BlockMeta):

    def __init__(self):
        self.name = "FunctionSource"
        self.category = "sources"
        self.type = "function_source"
        self.summary = "User-defined source block y = f(t, dt)."
        self.description = (
            "This block evaluates a user-provided Python function with no inputs:\n\n"
            "    y = f(t, dt)\n\n"
            "The function is loaded from an external Python file and executed at each\n"
            "activation. The output is exposed on the `out` port."
        )

        self.parameters = [
            ParameterMeta(
                name="file_path",
                type="string",
                required=True,
                description=(
                    "Path to the Python file containing the function, relative to "
                    "the project.yaml file."
                ),
            ),
            ParameterMeta(
                name="function_name",
                type="string",
                required=True,
                description="Name of the function to call inside the Python file.",
            ),
            ParameterMeta(
                name="sample_time",
                type="float",
                description="Optional execution period of the block.",
            ),
        ]

        self.outputs = [
            PortMeta(
                name="out",
                display_as="out",
                shape=["n", "m"],
                description="Function output signal.",
            )
        ]

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
