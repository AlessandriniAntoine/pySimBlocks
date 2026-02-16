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

from typing import TYPE_CHECKING

from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from pySimBlocks.gui.dialogs.help_dialog import HelpDialog

if TYPE_CHECKING:
    from pySimBlocks.gui.graphics.block_item import BlockItem


class BlockDialog(QDialog):
    def __init__(self,
                 block: 'BlockItem',
                 readonly: bool = False
    ):
        super().__init__()
        self.block = block
        self.meta = block.instance.meta
        self.instance = block.instance

        self.readonly = readonly
        if self.readonly:
            self.setWindowTitle(f"[{self.block.instance.name}] Information")
        else:
            self.setWindowTitle(f"Edit [{self.block.instance.name}] Parameters")
        self.setMinimumWidth(300)

        main_layout = QVBoxLayout(self)
        project_dir = None
        if hasattr(self.block, "view") and self.block.view is not None:
            controller = getattr(self.block.view, "project_controller", None)
            if controller is not None and controller.project_state is not None:
                project_dir = controller.project_state.directory_path

        self.session = self.meta.create_dialog_session(self.instance, project_dir)
        self.build_meta_layout(main_layout)
        self.build_buttons_layout(main_layout)

    # --------------------------------------------------------------------------
    # Dialog Layout Methods
    # --------------------------------------------------------------------------
    def build_meta_layout(self, layout: QVBoxLayout):
        form = QFormLayout()
        self.meta.build_description(form)
        self.meta.build_pre_param(self.session, form, self.readonly)
        self.meta.build_param(self.session, form, self.readonly)
        self.meta.build_post_param(self.session, form, self.readonly)
        layout.addLayout(form)
        self.meta.refresh_form(self.session)

    def build_buttons_layout(self, layout: QVBoxLayout):
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

        if self.readonly:
            ok_btn.setEnabled(False)
            apply_btn.setEnabled(False)

        layout.addLayout(buttons_layout)


    # --------------------------------------------------------------------------
    # Button Methods
    # --------------------------------------------------------------------------
    def apply(self):
        if self.readonly:
            return

        params = self.meta.gather_params(self.session)
        self.block.view.update_block_param_event(self.block.instance, params)

    # ------------------------------------------------------------
    def ok(self):
        self.apply()
        self.accept()

    # ------------------------------------------------------------
    def open_help(self):
        help_path = self.block.instance.meta.doc_path

        if help_path and help_path.exists():
            HelpDialog(help_path, self).exec()
        else:
            QMessageBox.information(self, "Help", "No documentation available.")
