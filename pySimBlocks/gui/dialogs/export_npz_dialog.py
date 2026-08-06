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

from __future__ import annotations

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView, QDialog, QDialogButtonBox, QFormLayout, QHeaderView,
    QLabel, QSpinBox, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from pySimBlocks.project.plot_series import stack_logged_signal


class ExportNpzDialog(QDialog):
    """Dialog letting the user pick which logged signals to export to .npz.

    Displays one row per available signal, with a checkbox (checked by
    default) controlling whether the signal is exported, and an editable
    field for the key name to use in the resulting .npz archive.

    Attributes:
        logs: Mapping of signal name to the corresponding logged array.
        table: Table widget holding one row per signal.
    """

    def __init__(self, logs: dict[str, np.ndarray], 
                 key_names: dict[str, str], 
                 decimation: int = 1,
                 parent=None):
        """Initialize the export dialog and populate it from the logs.

        Args:
            logs: Mapping of signal name to the corresponding logged array.
            parent: Optional parent widget.

        Raises:
            None.
        """
        super().__init__(parent)
        self.setWindowTitle("Export to .npz")
        self.resize(420, 400)

        self.logs = logs

        layout = QVBoxLayout(self)

        # -------- Decimation --------
        deci_row = QWidget()
        deci_layout = QFormLayout(deci_row)
        deci_layout.setContentsMargins(0, 0, 0, 8)
        self.decimation_spin = QSpinBox()
        self.decimation_spin.setMinimum(1)
        self.decimation_spin.setMaximum(1_000_000)
        self.decimation_spin.setValue(max(1, decimation))
        self.decimation_spin.setToolTip("Keep 1 sample every N (1 = no decimation)")
        deci_layout.addRow("Decimation (keep 1 in N):", self.decimation_spin)
        layout.addWidget(deci_row)

        self.table = QTableWidget(len(logs), 3, self)
        self.table.setHorizontalHeaderLabels(["Export", "Variable", "Key name"])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)

        for row, key in enumerate(self.logs.keys()):
            check_item = QTableWidgetItem()
            check_item.setFlags(
                (check_item.flags() | Qt.ItemIsUserCheckable) & ~Qt.ItemIsEditable
            )
            check_item.setCheckState(Qt.Checked)
            self.table.setItem(row, 0, check_item)

            var_item = QTableWidgetItem(key)
            var_item.setFlags(var_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 1, var_item)

            default_name = key_names.get(key, key)
            name_item = QTableWidgetItem(default_name)
            self.table.setItem(row, 2, name_item)

        layout.addWidget(self.table)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    # --------------------------------------------------------------------------
    # Public Methods
    # --------------------------------------------------------------------------

    def decimation_value(self) -> int:
        """Return the decimation factor entered by the user."""
        return self.decimation_spin.value()

    def selected_arrays(self) -> dict[str, np.ndarray]:
        """Return the arrays selected for export, keyed by their edited name.

        Each signal is stacked over time (``logs`` stores raw per-step
        samples as lists, pySimBlocks' internal representation) and a
        trailing singleton axis is dropped, since every signal is logged
        internally as a 2D column vector even when it is a scalar.

        Returns:
            Mapping of (possibly renamed) key to the ready-to-save array,
            containing only the rows whose checkbox is checked. If two rows
            end up with the same key name, the last one wins.
        """
        result: dict[str, np.ndarray] = {}
        for row, original_key in enumerate(self.logs.keys()):
            check_item = self.table.item(row, 0)
            if check_item.checkState() != Qt.Checked:
                continue
            name_item = self.table.item(row, 2)
            key = name_item.text().strip() or original_key
            result[key] = self._stack(original_key)
        return result

    def key_mapping(self) -> dict[str, str]:
        """Return the current variable -> key-name mapping (all rows, even unchecked)."""
        mapping = {}
        for row, original_key in enumerate(self.logs.keys()):
            name_item = self.table.item(row, 2)
            mapping[original_key] = name_item.text().strip() or original_key
        return mapping

    # --------------------------------------------------------------------------
    # Private Methods
    # --------------------------------------------------------------------------

    def _stack(self, original_key: str) -> np.ndarray:
        """Stack the raw per-step samples of a signal and drop a trailing
        singleton axis.

        Args:
            original_key: Log key as stored in ``self.logs`` (unrenamed).

        Returns:
            Stacked array, ``(T,)`` for ``time`` and ``(T, *sample_shape)``
            (trailing size-1 axis squeezed) for every other signal.
        """
        n = self.decimation_spin.value()
        if original_key == "time":
            arr = np.asarray(self.logs[original_key]).flatten()
            return arr[::n]

        arr = stack_logged_signal(self.logs, original_key)
        if arr.ndim >= 2 and arr.shape[-1] == 1:
            arr = arr.squeeze(-1)
        return arr[::n]
