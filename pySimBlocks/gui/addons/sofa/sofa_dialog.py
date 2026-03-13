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
    """Configure and launch SOFA integration actions from the GUI.

    Attributes:
        sofa_service: Service handling SOFA detection, export, and execution.
    """

    def __init__(self, sofa_service: SofaService, parent=None):
        """Initialize the SOFA dialog.

        Args:
            sofa_service: Service handling SOFA integration.
            parent: Optional parent widget.

        Raises:
            None.
        """
        super().__init__(parent)
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

    # --------------------------------------------------------------------------
    # Public Methods
    # --------------------------------------------------------------------------

    def build_form(self, layout):
        """Build the SOFA configuration form.

        Args:
            layout: Parent layout receiving the form.
        """
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

    def apply(self):
        """Validate and apply the SOFA executable path.

        Returns:
            True if the SOFA path is valid, otherwise False.
        """
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
        """Apply the current values and close the dialog."""
        if not self.apply():
            return
        self.accept()

    def run(self):
        """Run the current SOFA scene through the configured service."""
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
        try:
            ok, title, details = self.sofa_service.run()
        except Exception as e:
            ok, title, details = False, "Error launching SOFA", str(e)
        finally:
            progress.close()
        if not ok:
            dialog = LogDialog(
                title=f"SOFA error – {title}",
                content=details,
                parent=self
            )
            dialog.exec()

    def export(self):
        """Export the SOFA controller for the current project."""
        if not self.apply():
            return
        if not self._update_scene_file():
            return
        window = self.parent()
        self.sofa_service.export_controller(window, window.saver)

    # --------------------------------------------------------------------------
    # Private Methods
    # --------------------------------------------------------------------------

    def _on_gui_changed(self, value):
        """Update the selected SOFA GUI backend."""
        self.sofa_service.gui = value

    def _update_scene_file(self):
        """Validate and cache the scene file through the SOFA service."""
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
    """Display execution logs in a read-only dialog.

    Attributes:
        text: Read-only text area showing the log content.
    """

    def __init__(self, title: str, content: str, parent=None):
        """Initialize the log dialog.

        Args:
            title: Dialog title.
            content: Log text to display.
            parent: Optional parent widget.

        Raises:
            None.
        """
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
