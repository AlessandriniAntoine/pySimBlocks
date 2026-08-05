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

from typing import Any, Dict, List, Tuple

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

# Parameter types (see ParameterMeta.type) considered numeric enough to be
# exposed as an ImGui slider at runtime.
NUMERIC_PARAM_TYPES = {
    "float",
    "int",
    "scalar",
    "vector",
    "matrix",
    "scalar | vector | matrix",
}

# Block types excluded from the candidate list: sliding a SOFA I/O block's
# own attributes does not make sense (it is the block driving the sliders).
_EXCLUDED_BLOCK_TYPES = {"sofa_plant", "sofa_exchange_i_o"}


def collect_slider_candidates(project_state) -> List[Tuple[str, str, str]]:
    """List every block/parameter pair eligible as a SOFA slider.

    Candidates are derived from static block metadata (``ParameterMeta``),
    not from a live SOFA/pySimBlocks instance, so this works from the GUI
    before any simulation is run.

    Args:
        project_state: Project state holding the current block instances.

    Returns:
        Sorted list of ``(block_name, param_name, description)`` tuples.
    """
    candidates: List[Tuple[str, str, str]] = []
    for block in getattr(project_state, "blocks", []):
        if block.meta.type in _EXCLUDED_BLOCK_TYPES:
            continue
        for pmeta in block.meta.parameters:
            if pmeta.type not in NUMERIC_PARAM_TYPES:
                continue
            candidates.append((block.name, pmeta.name, pmeta.description))

    candidates.sort(key=lambda c: (c[0].lower(), c[1].lower()))
    return candidates


class SliderParamsDialog(QDialog):
    """Table-based editor for the ``slider_params`` SOFA parameter.

    Lists every numeric parameter declared by the blocks of the current
    project (from static metadata) and lets the user check the ones to
    expose as ImGui sliders, together with a min/max range each. A filter
    field narrows the list down when the project has many blocks.

    Attributes:
        project_state: Project state used to enumerate candidate variables.
        table: Table widget listing candidate variables.
        rows: Row widgets keyed by ``"block_name.param_name"``.
    """

    def __init__(
        self,
        project_state,
        current_value: Dict[str, Any] | None,
        parent=None,
    ):
        """Initialize the slider-params dialog.

        Args:
            project_state: Project state used to enumerate candidate variables.
            current_value: Current ``slider_params`` dict, used to pre-check
                rows and pre-fill their min/max values.
            parent: Optional parent widget.

        Raises:
            None.
        """
        super().__init__(parent)
        self.setWindowTitle("Configure SOFA sliders")
        self.setMinimumWidth(480)

        self.project_state = project_state
        self._current_value = dict(current_value) if current_value else {}
        self.rows: Dict[str, Dict[str, Any]] = {}

        main_layout = QVBoxLayout(self)

        self._build_filter_row(main_layout)
        self._build_table(main_layout)
        self._populate_table()
        self._build_buttons_row(main_layout)

        # Cap the dialog height for diagrams with many variables; the table
        # itself scrolls for whatever does not fit.
        row_count = max(self.table.rowCount(), 1)
        self.resize(560, min(140 + 28 * row_count, 520))

    # --------------------------------------------------------------------------
    # Public Methods
    # --------------------------------------------------------------------------

    def slider_params(self) -> Dict[str, List[float]]:
        """Build the ``slider_params`` dict from the checked rows.

        Returns:
            Mapping of ``"block_name.param_name"`` to ``[min, max]`` for
            every row whose checkbox is checked.
        """
        result: Dict[str, List[float]] = {}
        for key, widgets in self.rows.items():
            if widgets["check"].isChecked():
                result[key] = [widgets["min"].value(), widgets["max"].value()]
        return result

    def accept(self) -> None:
        """Validate ranges before closing the dialog."""
        for key, widgets in self.rows.items():
            if not widgets["check"].isChecked():
                continue
            if widgets["min"].value() >= widgets["max"].value():
                QMessageBox.warning(
                    self,
                    "Invalid range",
                    f"'{key}': min must be strictly less than max.",
                )
                return
        super().accept()

    # --------------------------------------------------------------------------
    # Private Methods
    # --------------------------------------------------------------------------

    def _build_filter_row(self, layout: QVBoxLayout) -> None:
        """Build the free-text filter row."""
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter:"))
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("Filter by block or parameter name...")
        self.filter_edit.textChanged.connect(self._apply_filter)
        filter_layout.addWidget(self.filter_edit)
        layout.addLayout(filter_layout)

    def _build_table(self, layout: QVBoxLayout) -> None:
        """Build the empty candidate-variable table."""
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["", "Variable", "Range (min – max)"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

    def _build_buttons_row(self, layout: QVBoxLayout) -> None:
        """Build the Ok/Cancel button row."""
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        ok_btn = QPushButton("Ok")
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(ok_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        layout.addLayout(buttons_layout)

    def _populate_table(self) -> None:
        """Fill the table with one row per candidate variable."""
        candidates = collect_slider_candidates(self.project_state)
        self.table.setRowCount(len(candidates))

        for row, (block_name, param_name, description) in enumerate(candidates):
            key = f"{block_name}.{param_name}"
            checked = key in self._current_value
            bounds = self._current_value.get(key, [0.0, 1.0])

            check = QCheckBox()
            check.setChecked(checked)
            check_container = QWidget()
            check_layout = QHBoxLayout(check_container)
            check_layout.setContentsMargins(0, 0, 0, 0)
            check_layout.setAlignment(Qt.AlignCenter)
            check_layout.addWidget(check)
            self.table.setCellWidget(row, 0, check_container)

            name_item = QTableWidgetItem(key)
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            if description:
                name_item.setToolTip(description)
            self.table.setItem(row, 1, name_item)

            range_widget = QWidget()
            range_layout = QHBoxLayout(range_widget)
            range_layout.setContentsMargins(0, 0, 0, 0)

            min_spin = QDoubleSpinBox()
            min_spin.setRange(-1e6, 1e6)
            min_spin.setDecimals(4)
            min_spin.setValue(float(bounds[0]))
            min_spin.setEnabled(checked)

            max_spin = QDoubleSpinBox()
            max_spin.setRange(-1e6, 1e6)
            max_spin.setDecimals(4)
            max_spin.setValue(float(bounds[1]))
            max_spin.setEnabled(checked)

            range_layout.addWidget(min_spin)
            range_layout.addWidget(QLabel("–"))
            range_layout.addWidget(max_spin)
            self.table.setCellWidget(row, 2, range_widget)

            check.toggled.connect(min_spin.setEnabled)
            check.toggled.connect(max_spin.setEnabled)

            self.rows[key] = {
                "check": check,
                "min": min_spin,
                "max": max_spin,
                "block": block_name,
                "param": param_name,
            }

    def _apply_filter(self, text: str) -> None:
        """Hide rows whose variable name does not match the filter text."""
        needle = text.strip().lower()
        for row in range(self.table.rowCount()):
            key = self.table.item(row, 1).text().lower()
            self.table.setRowHidden(row, needle not in key)


class SliderParamsRowMixin:
    """Mixin adding a "Configure sliders..." row for the ``slider_params`` param.

    Mix this into a ``BlockMeta`` subclass (before ``BlockMeta`` in the MRO)
    and call :meth:`_build_slider_params_row` from ``build_param`` instead of
    the generic ``_create_param_row`` for the ``slider_params`` parameter.
    """

    def _build_slider_params_row(
        self,
        session,
        form: QFormLayout,
        pmeta,
        readonly: bool = False,
    ) -> None:
        """Build the summary label + "Configure..." button row.

        Args:
            session: Active dialog session.
            form: Form layout receiving the widget.
            pmeta: ``ParameterMeta`` for ``slider_params``.
            readonly: Whether the dialog is read-only.
        """
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)

        summary = QLabel()
        configure_btn = QPushButton("Configure sliders...")
        configure_btn.setEnabled(not readonly)
        configure_btn.clicked.connect(
            lambda: self._open_slider_params_dialog(session, summary)
        )

        row_layout.addWidget(summary, 1)
        row_layout.addWidget(configure_btn)

        label = QLabel(f"{pmeta.name}:")
        if pmeta.description:
            label.setToolTip(pmeta.description)

        form.addRow(label, row_widget)
        session.param_widgets[pmeta.name] = row_widget
        session.param_labels[pmeta.name] = label

        self._refresh_slider_summary(session, summary)

    def _refresh_slider_summary(self, session, summary_label: QLabel) -> None:
        """Update the summary label from the current local parameter state."""
        value = session.local_params.get("slider_params") or {}
        count = len(value) if isinstance(value, dict) else 0
        summary_label.setText(
            f"{count} variable(s) configured" if count else "No sliders configured"
        )

    def _open_slider_params_dialog(self, session, summary_label: QLabel) -> None:
        """Open the slider-params table dialog and apply the result."""
        if session.project_state is None:
            QMessageBox.information(
                None,
                "Unavailable",
                "Open this block's dialog from the diagram to list project variables.",
            )
            return

        current = session.local_params.get("slider_params") or {}
        dialog = SliderParamsDialog(session.project_state, current)
        if dialog.exec() == QDialog.Accepted:
            session.local_params["slider_params"] = dialog.slider_params()
            self._refresh_slider_summary(session, summary_label)
