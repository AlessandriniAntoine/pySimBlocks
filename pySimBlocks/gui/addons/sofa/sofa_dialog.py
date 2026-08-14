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
    QApplication,
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
from PySide6.QtGui import QTextCursor, QTextCharFormat, QColor, QFont
from shiboken6 import isValid

from pySimBlocks.gui.addons.sofa.sofa_service import SofaService


class SofaDialog(QDialog):
    """Configure and launch SOFA integration actions from the GUI.

    Non-modal: the dialog is shown/hidden (never exec'd), and is meant to
    be created once and reused (see ToolBarView.on_open_sofa_dialog) so it
    keeps its state and position across multiple runs.

    Attributes:
        sofa_service: Service handling SOFA detection, export, and execution.
        log_window: Reused, non-modal window streaming SOFA's stdout/stderr.
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
        self.log_window: SofaLogWindow | None = None

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
        self.run_btn = QPushButton("runSofa")
        self.run_btn.clicked.connect(self.run)
        form.addRow(label, self.run_btn)

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
        """Apply the current values and hide the dialog (instance is reused)."""
        if not self.apply():
            return
        self.hide()

    def run(self):
        """Run the current SOFA scene through the configured service."""
        if not self.apply():
            return
        if not self._update_scene_file():
            return

        if self.log_window is None or not isValid(self.log_window):
            self.log_window = SofaLogWindow(parent=self)
        else:
            self.log_window.reset()

        self.run_btn.setEnabled(False)
        self.sofa_service.on_early_warning = self._show_early_warning

        try:
            started, title, details = self.sofa_service.start(
                on_output=self.log_window.append_log,
                on_result=self._on_sofa_result,
            )
        except Exception as e:
            started, title, details = False, "Error launching SOFA", str(e)

        if not started:
            self.run_btn.setEnabled(True)
            QMessageBox.warning(self, title, details)
            return

        self.log_window.show()
        self.log_window.raise_()
        self.log_window.activateWindow()

    def _on_sofa_result(self, ok: bool, title: str, details: str):
        """Handle the final outcome reported by the SOFA service."""
        self.run_btn.setEnabled(True)
        self.log_window.set_finished(ok, title, details)
        if ok:
            self.sofa_service.project_state.logs = self.sofa_service.logs
            if self.sofa_service.on_finished:
                self.sofa_service.on_finished()

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

    def _show_early_warning(self, message: str):
        """Show an immediate warning while SOFA is still running."""
        QMessageBox.warning(self, "Project YAML mismatch", message)



class SofaLogWindow(QDialog):
    """Non-modal window streaming SOFA's stdout/stderr in real time.

    Stays open after the run finishes (success or failure) so the user
    can scroll back through the full log and copy it for a bug report.
    Error/warning lines are highlighted as they arrive. The window is
    meant to be created once by SofaDialog and reused across runs via
    ``reset()``.

    Attributes:
        text: Read-only text area showing the accumulated log content.
        status_label: One-line status shown above the log area.
        close_btn: Button enabled once the current run has finished.
    """

    def __init__(self, parent=None):
        """Initialize the log window.

        Args:
            parent: Optional parent widget.

        Raises:
            None.
        """
        super().__init__(parent)
        self.setModal(False)
        self.resize(900, 550)

        layout = QVBoxLayout(self)

        self.status_label = QLabel()
        layout.addWidget(self.status_label)

        self.text = QPlainTextEdit()
        self.text.setReadOnly(True)
        self.text.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.text.setFont(QFont("Monospace"))
        layout.addWidget(self.text)

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        copy_btn = QPushButton("Copy log")
        copy_btn.clicked.connect(self._copy_log)
        buttons_layout.addWidget(copy_btn)

        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.hide)
        buttons_layout.addWidget(self.close_btn)

        layout.addLayout(buttons_layout)

        self.reset()

    # --------------------------------------------------------------------------
    # Public Methods
    # --------------------------------------------------------------------------

    def reset(self):
        """Clear the log and status to prepare the window for a new run."""
        self.setWindowTitle("SOFA running…")
        self.status_label.setText(
            "SOFA is running. Close the SOFA GUI window to finish."
        )
        self.status_label.setStyleSheet("")
        self.text.clear()
        self.close_btn.setEnabled(False)

    def append_log(self, chunk: str):
        """Append a chunk of streamed output, highlighting error/warning lines.

        Args:
            chunk: Raw text chunk emitted by the running process.
        """
        cursor = self.text.textCursor()
        cursor.movePosition(QTextCursor.End)
        for line in chunk.splitlines(keepends=True):
            fmt = QTextCharFormat()
            if "ERROR" in line:
                fmt.setForeground(QColor("#d63031"))
            elif "WARN" in line or "DEPRECATED" in line:
                fmt.setForeground(QColor("#e08e0b"))
            cursor.setCharFormat(fmt)
            cursor.insertText(line)
        self.text.setTextCursor(cursor)
        self.text.ensureCursorVisible()

    def set_finished(self, ok: bool, title: str, details: str):
        """Mark the run as finished and update the status banner.

        Args:
            ok: Whether the run succeeded.
            title: Short outcome title.
            details: Full details/log to append if not already shown.
        """
        self.close_btn.setEnabled(True)
        if ok:
            self.setWindowTitle("SOFA finished")
            self.status_label.setText(f"✔ {title}")
            self.status_label.setStyleSheet("color: #2e7d32; font-weight: bold;")
        else:
            self.setWindowTitle(f"SOFA error – {title}")
            self.status_label.setText(f"✘ {title}")
            self.status_label.setStyleSheet("color: #d63031; font-weight: bold;")
            if details and details not in self.text.toPlainText():
                self.append_log("\n" + details + "\n")

    # --------------------------------------------------------------------------
    # Private Methods
    # --------------------------------------------------------------------------

    def _copy_log(self):
        """Copy the full log content to the clipboard."""
        QApplication.clipboard().setText(self.text.toPlainText())
