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
    QDialog, QLabel, QPushButton,
    QHBoxLayout, QVBoxLayout, QStyle
)
from PySide6.QtCore import Qt


class UnsavedChangesDialog(QDialog):
    SAVE = 1
    DISCARD = 2
    CANCEL = 3

    def __init__(self, action_name: str, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Unsaved changes")
        self.setModal(True)

        self.setWindowFlags(
            Qt.Dialog |
            Qt.WindowTitleHint |
            Qt.WindowCloseButtonHint
        )

        # --- Icon (same as QMessageBox warning) ---
        icon_label = QLabel()
        icon = self.style().standardIcon(QStyle.SP_MessageBoxWarning)
        icon_label.setPixmap(icon.pixmap(64, 64))
        icon_label.setAlignment(Qt.AlignTop)

        # --- Text ---
        text_label = QLabel(
            "<b>The project has unsaved changes."
            f"Do you want to save your changes before {action_name}?"
        )
        text_label.setWordWrap(True)

        text_layout = QVBoxLayout()
        text_layout.addWidget(text_label)

        content_layout = QHBoxLayout()
        content_layout.addWidget(icon_label)
        content_layout.addLayout(text_layout)

        # --- Buttons (order EXACT) ---
        yes_btn = QPushButton("Yes")
        no_btn = QPushButton("No")
        cancel_btn = QPushButton("Cancel")

        yes_btn.clicked.connect(lambda: self.done(self.SAVE))
        no_btn.clicked.connect(lambda: self.done(self.DISCARD))
        cancel_btn.clicked.connect(lambda: self.done(self.CANCEL))

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        buttons_layout.addWidget(yes_btn)
        buttons_layout.addWidget(no_btn)
        buttons_layout.addWidget(cancel_btn)

        # --- Main layout ---
        layout = QVBoxLayout(self)
        layout.addLayout(content_layout)
        layout.addSpacing(12)
        layout.addLayout(buttons_layout)

    # ❌ Esc does nothing
    def reject(self):
        pass

    # ❌ Close button (X) does nothing
    def closeEvent(self, event):
        event.ignore()
