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
from typing import Any, Dict

from PySide6.QtWidgets import QFormLayout, QLabel, QLineEdit, QPushButton

from pySimBlocks.gui.blocks.block_meta import BlockMeta
from pySimBlocks.gui.blocks.parameter_meta import ParameterMeta
from pySimBlocks.gui.blocks.port_meta import PortMeta


class FileSourceMeta(BlockMeta):

    def __init__(self):
        self.name = "FileSource"
        self.category = "sources"
        self.type = "file_source"
        self.summary = "Read a sequence of samples from a CSV, NPY, or NPZ file."
        self.description = (
            "Loads samples from file and outputs one sample per simulation step.\n\n"
            "- `.npz`: reads one array from the archive (`key` mandatory).\n"
            "- `.npy`: reads one array from a NPY file (`key` unused).\n"
            "- `.csv`: reads one numeric CSV column (`key` = column name).\n\n"
            "Each step emits one row as a column vector."
        )

        self.parameters = [
            ParameterMeta(
                name="file_path",
                type="str",
                required=True,
                description="Path to the source file."
            ),
            ParameterMeta(
                name="key",
                type="str",
                description="NPZ array key or CSV column name."
            ),
            ParameterMeta(
                name="repeat",
                type="enum",
                autofill=True,
                default=False,
                enum=[False, True],
                description="If true, replay samples from the beginning after end of file."
            ),
            ParameterMeta(
                name="use_time",
                type="enum",
                autofill=True,
                default=False,
                enum=[False, True],
                description="If true (NPZ/CSV), use 'time' data and apply ZOH at simulation time t."
            ),
            ParameterMeta(
                name="sample_time",
                type="float",
                description="Block execution period."
            ),
        ]

        self.outputs = [
            PortMeta(
                name="out",
                display_as="out",
                shape=["n", 1],
                description="Current output sample."
            )
        ]

    # ------------------------------------------------------
    def is_parameter_active(self, 
                            param_name: str, 
                            instance_params: Dict[str, Any]) -> bool:
        file_path = str(instance_params.get("file_path", "") or "")
        ext = file_path.rsplit(".", 1)[-1].lower() if "." in file_path else ""

        if param_name == "key":
            return ext in {"npz", "csv"}

        if param_name == "use_time":
            return ext in {"npz", "csv"}

        return super().is_parameter_active(param_name, instance_params)

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
            if pmeta.name == "file_path":
                self.build_file_param_row(
                    session,
                    form,
                    pmeta,
                    readonly=readonly,
                    file_filter="Data files (*.npz *.npy *.csv);;All files (*)",
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
