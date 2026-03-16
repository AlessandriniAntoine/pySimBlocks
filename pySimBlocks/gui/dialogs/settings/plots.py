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
    QWidget, QHBoxLayout, QVBoxLayout, QListWidget, QListWidgetItem,
    QLabel, QLineEdit, QPushButton, QMessageBox
)
from PySide6.QtCore import Qt

from pySimBlocks.gui.models.project_state import ProjectState
from pySimBlocks.gui.project_controller import ProjectController


class PlotSettingsWidget(QWidget):
    """Edit the set of named plots stored in the project.

    Attributes:
        project_state: Project state edited by the widget.
        project_controller: Controller applying plot changes.
        edit_index: Index of the plot currently being edited, or None.
    """

    def __init__(self, project_state: ProjectState, project_controller: ProjectController):
        """Initialize the plot settings widget.

        Args:
            project_state: Project state edited by the widget.
            project_controller: Controller applying plot changes.

        Raises:
            None.
        """
        super().__init__()
        self.project_state = project_state
        self.project_controller = project_controller
        self.edit_index = None

        main = QHBoxLayout(self)

        # ==================================================
        # Left: plot list + actions
        # ==================================================
        left = QVBoxLayout()

        left.addWidget(QLabel("Plots"))

        self.plot_list = QListWidget()
        self.plot_list.currentRowChanged.connect(self.load_plot)
        left.addWidget(self.plot_list)

        self.new_btn = QPushButton("New")
        self.save_btn = QPushButton("Save")
        self.del_btn = QPushButton("Delete")

        self.new_btn.clicked.connect(self.new_plot)
        self.save_btn.clicked.connect(self.save_plot)
        self.del_btn.clicked.connect(self.delete_plot)

        left.addWidget(self.new_btn)
        left.addWidget(self.save_btn)
        left.addWidget(self.del_btn)

        main.addLayout(left, 1)

        # ==================================================
        # Right: editor
        # ==================================================
        right = QVBoxLayout()

        right.addWidget(QLabel("Title:"))
        self.title_edit = QLineEdit()
        right.addWidget(self.title_edit)

        right.addWidget(QLabel("Signals:"))
        self.signal_list = QListWidget()
        self.signal_list.setSelectionMode(QListWidget.NoSelection)
        right.addWidget(self.signal_list)

        main.addLayout(right, 2)

        self.refresh_plot_list()
        self.populate_signal_list()
        self.update_buttons_state()

    # --------------------------------------------------------------------------
    # Public Methods
    # --------------------------------------------------------------------------

    def refresh_from_project(self):
        """Synchronize the plot editor with the current project state."""
        self.edit_index = None
        self.refresh_plot_list()
        self.plot_list.clearSelection()
        self.populate_signal_list()
        self.title_edit.clear()
        self.update_buttons_state()

    def refresh_plot_list(self):
        """Refresh the plot titles shown in the list widget."""
        self.plot_list.clear()
        for plot in self.project_state.plots:
            self.plot_list.addItem(plot["title"])

    def populate_signal_list(self, checked=None):
        """Populate the signal checklist.

        Args:
            checked: Optional iterable of signal names to preselect.
        """
        self.signal_list.clear()
        checked = set(checked or [])

        for sig in self.project_state.get_output_signals():
            item = QListWidgetItem(sig)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if sig in checked else Qt.Unchecked)
            self.signal_list.addItem(item)

    def collect_selected_signals(self) -> list[str]:
        """Return the currently selected signal names.

        Returns:
            Selected signal names from the checklist.
        """
        return [
            self.signal_list.item(i).text()
            for i in range(self.signal_list.count())
            if self.signal_list.item(i).checkState() == Qt.Checked
        ]

    def reset_form(self):
        """Clear the editor fields and uncheck all signals."""
        self.title_edit.clear()
        self.populate_signal_list()

    def update_buttons_state(self):
        """Enable or disable actions based on the current selection state."""
        has_selection = self.plot_list.currentRow() >= 0
        self.del_btn.setEnabled(has_selection)

    def load_plot(self, index):
        """Load the selected plot into the editor.

        Args:
            index: Index of the plot selected in the list.
        """
        if index < 0:
            self.edit_index = None
            self.reset_form()
            self.update_buttons_state()
            return

        self.edit_index = index
        plot = self.project_state.plots[index]
        self.title_edit.setText(plot["title"])
        self.populate_signal_list(plot["signals"])
        self.update_buttons_state()


    def new_plot(self):
        """Start editing a new plot definition."""
        self.edit_index = None
        self.plot_list.clearSelection()
        self.reset_form()
        self.update_buttons_state()

    def save_plot(self):
        """Create or update the currently edited plot."""
        title = self.title_edit.text().strip()
        if not title:
            QMessageBox.warning(self, "Invalid plot", "Plot title cannot be empty.")
            return

        signals = self.collect_selected_signals()
        if not signals:
            QMessageBox.warning(self, "Invalid plot", "No signal selected.")
            return

        if self.edit_index is None:
            self.project_controller.create_plot(title, signals)
            self.refresh_plot_list()
        else:
            self.project_controller.update_plot(self.edit_index, title, signals)
            self.plot_list.item(self.edit_index).setText(title)

        self.update_buttons_state()


    def delete_plot(self):
        """Delete the currently selected plot."""
        if self.edit_index is None:
            return

        self.project_controller.delete_plot(self.edit_index)
        self.edit_index = None
        self.refresh_plot_list()
        self.plot_list.clearSelection()
        self.reset_form()
        self.update_buttons_state()
