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

from pathlib import Path
from PySide6.QtWidgets import (
    QHBoxLayout,
    QDialog,
    QLabel,
    QVBoxLayout,
    QLineEdit,
    QPushButton,
    QFormLayout,
    QComboBox,
    QMessageBox,
    QPlainTextEdit
)

from pySimBlocks.gui.addons.sofa.sofa_service import SofaService


class SofaDialog(QDialog):
    def __init__(self, sofa_service: SofaService):
        super().__init__()
        self.setWindowTitle("Edit block")
        self.setMinimumWidth(300)

        self.sofa_service = sofa_service

        main_layout = QVBoxLayout(self)
        self.build_form(main_layout)

        # --- Buttons row ---
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        ok_btn = QPushButton("Ok")
        ok_btn.setDefault(True)
        ok_btn.setAutoDefault(True)
        ok_btn.clicked.connect(self.ok)
        buttons_layout.addWidget(ok_btn)

        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self.apply)
        buttons_layout.addWidget(apply_btn)
        main_layout.addLayout(buttons_layout)

    # ------------------------------------------------------------
    # Form
    def build_form(self, layout):
        form = QFormLayout()

        # --- Block name ---
        self.run_edit = QLineEdit(self.sofa_service.sofa_path)
        self.run_edit.setText(self.sofa_service.sofa_path)
        label  = QLabel("runSofa:")
        label.setToolTip("runSofa path")
        form.addRow(label, self.run_edit)

        self.gui_combo = QComboBox()
        self.gui_combo.addItems(["imgui", "qglviewer", "qt", "custom"])
        self.gui_combo.setCurrentText(self.sofa_service.gui)
        self.gui_combo.currentTextChanged.connect(lambda val: self._on_gui_changed(val))
        form.addRow(QLabel("Sofa GUI:"), self.gui_combo)

        label = QLabel("Run diagram from Sofa:")
        label.setToolTip("Run simulation with sofa gui")
        run_btn = QPushButton("runSofa")
        run_btn.clicked.connect(self.run)
        form.addRow(label, run_btn)

        label = QLabel("Export Controller")
        label.setToolTip("Modify Sofa controller to run on cli.")
        export_btn = QPushButton("Export Controller")
        export_btn.clicked.connect(self.export)
        form.addRow(label, export_btn)

        layout.addLayout(form)

    # ------------------------------------------------------------
    # Buttons
    def apply(self):
        sofa_path = self.run_edit.text()
        if not Path(sofa_path).exists():
            QMessageBox.warning(
                self,
                "Invalid sofa path",
                f"The run sofa exec not exist:\n{sofa_path}",
            )
            return False
        self.sofa_service.sofa_path = sofa_path
        return True

    def ok(self):
        if not self.apply():
            return
        self.accept()

    def run(self):
        if not self.apply():
            return
        if not self._update_scene_file():
            return

        progress = QDialog(self)
        progress.setWindowTitle("SOFA running")
        progress.setModal(True)
        progress.setMinimumWidth(300)

        layout = QVBoxLayout(progress)
        layout.addWidget(QLabel(
            "SOFA is running.\n\n"
            "Close the SOFA GUI to return to pySimBlocks."
        ))

        progress.show()
        ok, title, details = self.sofa_service.run()
        progress.close()
        if not ok:
            dialog = LogDialog(
                title=f"SOFA error – {title}",
                content=details,
                parent=self
            )
            dialog.exec()

    def export(self):
        if not self.apply():
            return
        if not self._update_scene_file():
            return
        self.sofa_service.export_controlle()

    # ------------------------------------------------------------
    # internal methods
    def _on_gui_changed(self, value):
        self.sofa_service.gui = value

    def _update_scene_file(self):
        ok, msg, details = self.sofa_service.get_scene_file()
        if not ok:
            QMessageBox.warning(
                self,
                msg,
                details,
                QMessageBox.Ok
            )
        return ok



class LogDialog(QDialog):
    def __init__(self, title: str, content: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(800, 500)

        layout = QVBoxLayout(self)

        self.text = QPlainTextEdit()
        self.text.setReadOnly(True)
        self.text.setPlainText(content)
        self.text.setLineWrapMode(QPlainTextEdit.NoWrap)

        layout.addWidget(self.text)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
