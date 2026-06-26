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

import copy

import numpy as np
import matplotlib.pyplot as plt

from dataclasses import dataclass, field
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QVBoxLayout,
    QLabel, QTreeWidget, QTreeWidgetItem,
    QPushButton, QSizePolicy, QMessageBox, QComboBox, QToolButton, QMenu, QCheckBox,
    QSpinBox, QHeaderView, QLineEdit, QInputDialog,
)
from PySide6.QtCore import Qt

from matplotlib import gridspec
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT
from matplotlib.figure import Figure

from pySimBlocks.gui.models.project_state import ProjectState
from pySimBlocks.core.config import PlotConfig
from pySimBlocks.project.plot_from_config import plot_from_config
from pySimBlocks.gui.dialogs.plot_series_style_dialog import SeriesStyleDialog
from pySimBlocks.gui.project_controller import ProjectController
from pySimBlocks.project.plot_series import (
    DEFAULT_SERIES_STYLE,
    SeriesStyle,
    effective_style_for_component,
    flatten_series,
    is_manual_layout_plot,
    manual_layout_to_plot_dict,
    manual_state_from_layout_plot,
    plot_step_series_styled,
    resolve_series_style,
    series_from_signal,
    series_style_from_dict,
    series_style_to_dict,
)


@dataclass
class _ManualLayoutSession:
    """Holds all mutable state for the multi-panel manual plot editor."""

    selections: list[dict[str, set[str]]] = field(default_factory=lambda: [{}])
    titles: list[str] = field(default_factory=lambda: ["Plot 1"])
    active: int = 0
    panel_styles: list[dict[str, SeriesStyle]] = field(default_factory=lambda: [{}])

    @staticmethod
    def default_title(index: int) -> str:
        return f"Plot {index + 1}"

    def ensure_titles_aligned(self) -> None:
        while len(self.titles) < len(self.selections):
            self.titles.append(self.default_title(len(self.titles)))
        if len(self.titles) > len(self.selections):
            self.titles = self.titles[: len(self.selections)]

    def plot_title(self, index: int) -> str:
        self.ensure_titles_aligned()
        if 0 <= index < len(self.titles):
            text = self.titles[index].strip()
            if text:
                return text
        return self.default_title(index)

    def save_title(self, index: int, text: str) -> None:
        self.ensure_titles_aligned()
        idx = min(index, len(self.titles) - 1)
        self.titles[idx] = text

    def clamp_active(self) -> None:
        if not self.selections:
            self.active = 0
            return
        self.active = min(self.active, len(self.selections) - 1)

    def resize(self, value: int) -> None:
        old_count = len(self.selections)
        if value > old_count:
            for i in range(old_count, value):
                self.selections.append({})
                self.titles.append(self.default_title(i))
                self.panel_styles.append({})
        elif value < old_count:
            self.selections = self.selections[:value]
            self.titles = self.titles[:value]
            self.panel_styles = self.panel_styles[:value]
            if self.active >= value:
                self.active = max(0, value - 1)

    def remove_at(self, idx: int) -> None:
        del self.selections[idx]
        del self.titles[idx]
        del self.panel_styles[idx]
        new_count = len(self.selections)
        if self.active >= new_count:
            self.active = max(0, new_count - 1)

    def load_from_preset(self, plot: dict) -> None:
        selections, titles, panel_styles = manual_state_from_layout_plot(plot)
        if not selections:
            self.selections = [{}]
            self.titles = [self.default_title(0)]
            self.panel_styles = [{}]
        else:
            self.selections = selections
            self.titles = titles
            self.panel_styles = panel_styles
            while len(self.panel_styles) < len(self.selections):
                self.panel_styles.append({})
            self.panel_styles = self.panel_styles[: len(self.selections)]
        self.active = 0


@dataclass
class _ModePresetSession:
    """Holds mutable state for mode-based preset editing (styles + working cache)."""

    styles: dict[str, SeriesStyle] = field(default_factory=dict)
    working: dict[int, dict] = field(default_factory=dict, init=False, repr=False)

    def store(self, idx: int, signals: list[str], mode: str) -> None:
        self.working[idx] = {
            "signals": signals,
            "mode": mode,
            "styles": copy.deepcopy(self.styles),
        }

    def get_cached(self, idx: int) -> dict | None:
        return self.working.get(idx)

    def serialize_styles(self) -> dict[str, dict[str, str]]:
        out: dict[str, dict[str, str]] = {}
        for lbl, st in self.styles.items():
            data = series_style_to_dict(st)
            if data:
                out[str(lbl)] = data
        return out

    @staticmethod
    def styles_from_plot(plot: dict) -> dict[str, SeriesStyle]:
        styles: dict[str, SeriesStyle] = {}
        raw = plot.get("series_styles", {})
        if isinstance(raw, dict):
            for lbl, cfg in raw.items():
                if isinstance(cfg, dict):
                    styles[str(lbl)] = series_style_from_dict(cfg)
        return styles


class PlotDialog(QDialog):
    """Preview logged signals and launch configured plot windows.

    Attributes:
        project_state: Project state providing logs and plot definitions.
        signal tree selection: Checked signals/components for manual preview.
    """

    def __init__(
        self,
        project_state: ProjectState,
        project_controller: ProjectController | None = None,
        parent=None,
    ):
        """Initialize the plot dialog.

        Args:
            project_state: Project state providing logs and plot definitions.
            project_controller: Controller used to persist predefined plots.
            parent: Optional parent widget.

        Raises:
            None.
        """
        super().__init__(parent)
        self.project_controller = project_controller
        self.setWindowTitle("Plot signals")
        self.resize(900, 500)
        # fix fullscreen and minimize button not being available on certain environments
        self.setWindowFlags(
            Qt.Window
            | Qt.WindowTitleHint
            | Qt.WindowSystemMenuHint
            | Qt.WindowMinimizeButtonHint
            | Qt.WindowMaximizeButtonHint
            | Qt.WindowCloseButtonHint
        )

        self.project_state = project_state
        self._subplot_items: list[tuple[str, str]] = []
        self._subplot_actions: dict[str, object] = {}
        self._updating_signal_tree = False
        self._focused_panel_key: str | None = None
        self._axis_to_panel_key: dict[int, str] = {}
        self._manual = _ManualLayoutSession()
        self._mode = _ModePresetSession()
        self._last_preset_index: int | None = None

        self._build_ui()
        self._populate_signals()
        self._populate_plot_presets()
        self._manual.clamp_active()
        self._load_active_manual_title()
        self._sync_manual_controls_enabled()

    def present(self) -> None:
        """Show this window and refresh the preview from the latest logs."""
        self._flush_active_preset_working()
        self._populate_signals()
        self._populate_plot_presets()
        if self._uses_manual_layout():
            self._manual.clamp_active()
            self._load_active_manual_title()
            self._load_manual_selection_to_tree(
                self._manual.selections[self._manual.active]
            )
            self._refresh_all_tree_style_labels()
        elif self._is_mode_preset():
            idx = self._selected_preset_index()
            if idx is not None:
                self._load_mode_preset(idx)
        self._last_preset_index = self._selected_preset_index()
        self._update_preview_plot()
        self.show()
        self.raise_()
        self.activateWindow()

    # --------------------------------------------------------------------------
    # Private Methods
    # --------------------------------------------------------------------------
    @staticmethod
    def _disable_enter_key_activation(button: QPushButton) -> None:
        """Prevent Enter in a nearby line edit from clicking this button."""
        button.setAutoDefault(False)
        button.setDefault(False)

    def _build_ui(self):
        """Build the plot dialog user interface."""
        main_layout = QHBoxLayout(self)
        main_layout.addLayout(self._build_left_panel(), 0)
        main_layout.addLayout(self._build_right_panel(), 1)

    def _build_left_panel(self) -> QVBoxLayout:
        """Build and return the left control panel."""
        left_layout = QVBoxLayout()

        left_layout.addWidget(QLabel("<b>Manual plots</b>"))
        manual_count_row = QHBoxLayout()
        manual_count_row.addWidget(QLabel("Number of plots:"))
        self.manual_plot_count_spin = QSpinBox()
        self.manual_plot_count_spin.setMinimum(1)
        self.manual_plot_count_spin.setMaximum(12)
        self.manual_plot_count_spin.setValue(1)
        self.manual_plot_count_spin.setToolTip(
            "Number of manual plot panels. Decreasing the count removes the last plot only."
        )
        self.manual_plot_count_spin.valueChanged.connect(self._on_manual_plot_count_changed)
        manual_count_row.addWidget(self.manual_plot_count_spin)
        left_layout.addLayout(manual_count_row)

        manual_edit_title_row = QHBoxLayout()
        manual_edit_title_row.addWidget(QLabel("Title:"))
        self.manual_plot_title_edit = QLineEdit()
        self.manual_plot_title_edit.setPlaceholderText("Title of the selected plot panel")
        self.manual_plot_title_edit.setToolTip(
            "Click a plot panel in the preview to select it, then edit its title here."
        )
        self.manual_plot_title_edit.returnPressed.connect(self._on_manual_plot_title_edited)
        self.manual_plot_title_edit.editingFinished.connect(self._on_manual_plot_title_edited)
        manual_edit_title_row.addWidget(self.manual_plot_title_edit, 1)
        left_layout.addLayout(manual_edit_title_row)

        self.manual_remove_plot_btn = QPushButton("Remove selected plot")
        self.manual_remove_plot_btn.setToolTip(
            "Remove the plot panel selected in the preview and reduce the count by one."
        )
        self._disable_enter_key_activation(self.manual_remove_plot_btn)
        self.manual_remove_plot_btn.clicked.connect(self._on_manual_remove_selected_plot)
        left_layout.addWidget(self.manual_remove_plot_btn)

        self.save_preset_btn = QPushButton("Save plot preset")
        self.save_preset_btn.setToolTip(
            "Save the current plot preset (manual layout or mode-based). "
            "Overwrites the selected preset. Use Save project (Ctrl+S) for project.yaml."
        )
        self._disable_enter_key_activation(self.save_preset_btn)
        self.save_preset_btn.clicked.connect(self._save_plot_preset)
        left_layout.addWidget(self.save_preset_btn)

        left_layout.addWidget(QLabel("<b>Signals (logged)</b>"))

        self.signal_tree = QTreeWidget()
        self.signal_tree.setColumnCount(2)
        self.signal_tree.setHeaderLabels(["Signal", ""])
        self.signal_tree.setColumnWidth(1, 34)
        self.signal_tree.header().setStretchLastSection(False)
        self.signal_tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.signal_tree.itemChanged.connect(self._on_signal_toggled)
        left_layout.addWidget(self.signal_tree)

        left_layout.addWidget(QLabel("<b>Plot preset</b>"))
        self.plot_preset_combo = QComboBox()
        self.plot_preset_combo.currentIndexChanged.connect(self._on_plot_preset_changed)
        left_layout.addWidget(self.plot_preset_combo)

        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("Display mode:"))
        self.mode_preset_combo = QComboBox()
        for label, key in [
            ("Auto (recommended)", "auto"),
            ("Overlay (single axis)", "overlay"),
            ("Split by signal", "split_signals"),
            ("Split by component", "split_components"),
        ]:
            self.mode_preset_combo.addItem(label, key)
        self.mode_preset_combo.currentIndexChanged.connect(self._update_preview_plot)
        mode_row.addWidget(self.mode_preset_combo, 1)
        left_layout.addLayout(mode_row)

        left_layout.addWidget(QLabel("<b>Subplots filter</b>"))
        subplot_row = QHBoxLayout()
        self.subplot_menu_btn = QToolButton()
        self.subplot_menu_btn.setText("Select subplots")
        self.subplot_menu_btn.setPopupMode(QToolButton.InstantPopup)
        self.subplot_menu = QMenu(self.subplot_menu_btn)
        self.subplot_menu_btn.setMenu(self.subplot_menu)
        subplot_row.addWidget(self.subplot_menu_btn, 1)
        self.subplot_all_cb = QCheckBox("All")
        self.subplot_all_cb.setToolTip(
            "Checked: every subplot in the filter is shown. Uncheck to hide all, or use the menu for a partial selection."
        )
        self.subplot_all_cb.stateChanged.connect(self._on_subplot_all_cb_changed)
        self.subplot_all_cb.setEnabled(False)
        subplot_row.addWidget(self.subplot_all_cb)
        left_layout.addLayout(subplot_row)

        self.plot_defined_btn = QPushButton("Plot defined plots")
        self._disable_enter_key_activation(self.plot_defined_btn)
        self.plot_defined_btn.clicked.connect(self._plot_defined_plots)
        left_layout.addWidget(self.plot_defined_btn)

        return left_layout

    def _build_right_panel(self) -> QVBoxLayout:
        """Build and return the right plot preview panel."""
        self.figure = Figure()
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.canvas.mpl_connect("button_press_event", self._on_canvas_click)
        self.nav_toolbar = NavigationToolbar2QT(self.canvas, self)

        right_layout = QVBoxLayout()
        controls_layout = QHBoxLayout()
        self.grid_cb = QCheckBox("Grid")
        self.grid_cb.setChecked(True)
        self.grid_cb.stateChanged.connect(self._update_preview_plot)
        self.legend_cb = QCheckBox("Legend")
        self.legend_cb.setChecked(True)
        self.legend_cb.stateChanged.connect(self._update_preview_plot)
        self.autoscale_btn = QPushButton("Autoscale")
        self._disable_enter_key_activation(self.autoscale_btn)
        self.autoscale_btn.clicked.connect(self._autoscale_preview)
        controls_layout.addWidget(self.grid_cb)
        controls_layout.addWidget(self.legend_cb)
        controls_layout.addWidget(self.autoscale_btn)
        controls_layout.addStretch(1)

        right_layout.addLayout(controls_layout)
        right_layout.addWidget(self.nav_toolbar)
        right_layout.addWidget(self.canvas, 1)
        return right_layout

    def _populate_signals(self):
        """Populate the signal list from the available logged signals."""
        self.signal_tree.clear()
        self._updating_signal_tree = True
        try:
            for sig in sorted(self.project_state.logs.keys()):
                if sig == "time":
                    continue

                labels = self._component_labels_for_signal(sig)
                if len(labels) == 1:
                    self._add_scalar_signal_tree_row(sig, labels[0])
                    continue

                parent = QTreeWidgetItem([sig])
                parent.setFlags(parent.flags() | Qt.ItemIsUserCheckable)
                parent.setCheckState(0, Qt.Unchecked)
                parent.setData(0, Qt.UserRole, ("signal", sig))
                self.signal_tree.addTopLevelItem(parent)

                for label in labels:
                    child = QTreeWidgetItem([self._tree_label_for_component(label), ""])
                    child.setFlags(child.flags() | Qt.ItemIsUserCheckable)
                    child.setCheckState(0, Qt.Unchecked)
                    child.setData(0, Qt.UserRole, ("component", sig, label))
                    parent.addChild(child)
                    self._attach_style_button(child, label)
        finally:
            self._updating_signal_tree = False
        self._refresh_all_tree_style_labels()

    def _add_scalar_signal_tree_row(self, sig: str, label: str) -> None:
        """Add one top-level row for a scalar signal (single component, no expand)."""
        item = QTreeWidgetItem([self._tree_label_for_component(label), ""])
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
        item.setCheckState(0, Qt.Unchecked)
        item.setData(0, Qt.UserRole, ("component", sig, label))
        self.signal_tree.addTopLevelItem(item)
        self._attach_style_button(item, label)

    def _get_series_style(self, label: str, plot: dict | None = None) -> SeriesStyle:
        """Return merged style for a series (session overrides, then plot config)."""
        return resolve_series_style(label, self._mode.styles, plot)

    def _get_manual_series_style(self, panel_idx: int, label: str) -> SeriesStyle:
        """Style for one component in a manual-layout panel (per subplot)."""
        if 0 <= panel_idx < len(self._manual.panel_styles):
            st = self._manual.panel_styles[panel_idx].get(label)
            if st is not None:
                return st
        if self._is_manual_layout_preset():
            idx = self._selected_preset_index()
            if idx is not None:
                plot = self.project_state.plots[idx]
                return effective_style_for_component(plot, None, label)
        return SeriesStyle()

    def _tree_label_for_component(self, internal_label: str) -> str:
        """Text shown in the signal tree for one component."""
        if self._uses_manual_layout():
            name = self._get_manual_series_style(self._manual.active, internal_label).display_name.strip()
        else:
            plot = None
            idx = self._selected_preset_index()
            if idx is not None:
                p = self.project_state.plots[idx]
                if not is_manual_layout_plot(p):
                    plot = p
            name = self._get_series_style(internal_label, plot).display_name.strip()
        return name if name else internal_label

    def _refresh_tree_component_label(self, internal_label: str) -> None:
        """Update the signal tree row after a display name change."""
        for i in range(self.signal_tree.topLevelItemCount()):
            item = self.signal_tree.topLevelItem(i)
            data = item.data(0, Qt.UserRole)
            if isinstance(data, tuple) and len(data) == 3 and data[0] == "component":
                if str(data[2]) == internal_label:
                    item.setText(0, self._tree_label_for_component(internal_label))
                    return
                continue
            for c in range(item.childCount()):
                child = item.child(c)
                data = child.data(0, Qt.UserRole)
                if isinstance(data, tuple) and len(data) == 3 and str(data[2]) == internal_label:
                    child.setText(0, self._tree_label_for_component(internal_label))
                    return

    def _refresh_all_tree_style_labels(self) -> None:
        """Refresh visible names in the tree (needed when subplot context changes)."""
        for i in range(self.signal_tree.topLevelItemCount()):
            item = self.signal_tree.topLevelItem(i)
            data = item.data(0, Qt.UserRole)
            if isinstance(data, tuple) and len(data) == 3 and data[0] == "component":
                lbl = str(data[2])
                item.setText(0, self._tree_label_for_component(lbl))
                continue
            for c in range(item.childCount()):
                child = item.child(c)
                cdata = child.data(0, Qt.UserRole)
                if isinstance(cdata, tuple) and len(cdata) == 3 and cdata[0] == "component":
                    lbl = str(cdata[2])
                    child.setText(0, self._tree_label_for_component(lbl))

    def _attach_style_button(self, item: QTreeWidgetItem, label: str) -> None:
        """Add a style editor button on the right of a signal tree row."""
        btn = QPushButton("⚙")
        btn.setFixedSize(30, 22)
        self._disable_enter_key_activation(btn)
        btn.setToolTip(f"Line, marker, and color for « {label} »")
        btn.clicked.connect(lambda _checked=False, lbl=label: self._edit_series_style(lbl))
        self.signal_tree.setItemWidget(item, 1, btn)

    def _edit_series_style(self, label: str) -> None:
        """Open the style dialog for one series component."""
        if self._uses_manual_layout():
            pidx = self._manual.active
            while len(self._manual.panel_styles) <= pidx:
                self._manual.panel_styles.append({})
            current = self._manual.panel_styles[pidx].get(label, SeriesStyle())
        else:
            plot = None
            idx = self._selected_preset_index()
            if idx is not None:
                p = self.project_state.plots[idx]
                if not is_manual_layout_plot(p):
                    plot = p
            current = self._get_series_style(label, plot)
        dlg = SeriesStyleDialog(label, current, parent=self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        if self._uses_manual_layout():
            pidx = self._manual.active
            self._manual.panel_styles[pidx][label] = dlg.style()
        else:
            self._mode.styles[label] = dlg.style()
            if self._is_mode_preset():
                idx = self._selected_preset_index()
                if idx is not None:
                    self._store_mode_preset_working(idx)
        self._refresh_tree_component_label(label)
        self._update_preview_plot()

    def _on_signal_toggled(self, _item: QTreeWidgetItem, _column: int):
        """Redraw preview when signal/component check states change."""
        if self._updating_signal_tree:
            return
        self._updating_signal_tree = True
        try:
            data = _item.data(0, Qt.UserRole)
            if isinstance(data, tuple) and len(data) >= 2 and data[0] == "signal":
                # Parent toggled: apply state to all child components.
                for i in range(_item.childCount()):
                    _item.child(i).setCheckState(0, _item.checkState(0))
            elif isinstance(data, tuple) and len(data) == 3 and data[0] == "component":
                # Child toggled: keep parent check state in sync.
                parent = _item.parent()
                if parent is not None:
                    checked = 0
                    for i in range(parent.childCount()):
                        if parent.child(i).checkState(0) == Qt.Checked:
                            checked += 1
                    if checked == 0:
                        parent.setCheckState(0, Qt.Unchecked)
                    elif checked == parent.childCount():
                        parent.setCheckState(0, Qt.Checked)
        finally:
            self._updating_signal_tree = False
        if self._uses_manual_layout():
            self._save_active_manual_selection()
        elif self._is_mode_preset():
            idx = self._selected_preset_index()
            if idx is not None:
                self._store_mode_preset_working(idx)
        self._update_preview_plot()

    def _on_plot_preset_changed(self, _index: int):
        """Handle plot preset selection changes."""
        prev_idx = self._last_preset_index
        if prev_idx is not None and prev_idx != self._selected_preset_index():
            if 0 <= prev_idx < len(self.project_state.plots):
                if is_manual_layout_plot(self.project_state.plots[prev_idx]):
                    self._save_active_manual_selection()
                    self._save_active_manual_title()
                else:
                    self._store_mode_preset_working(prev_idx)

        layout_preset = self._is_manual_layout_preset()
        free_manual = self._is_manual_mode()
        mode_preset = self._is_mode_preset()
        self.signal_tree.setEnabled(free_manual or layout_preset or mode_preset)
        self._sync_manual_controls_enabled()
        self._sync_subplot_all_checkbox()
        if layout_preset:
            idx = self._selected_preset_index()
            if idx is not None:
                self._load_manual_state_from_layout_plot(self.project_state.plots[idx])
        elif mode_preset:
            idx = self._selected_preset_index()
            if idx is not None:
                self._load_mode_preset(idx)
        elif free_manual:
            self._load_manual_selection_to_tree(self._manual.selections[self._manual.active])
        self._last_preset_index = self._selected_preset_index()
        self._update_preview_plot()

    def _is_manual_mode(self) -> bool:
        """Return True when editing a free manual layout (not a saved preset)."""
        return self._selected_preset_index() is None

    def _is_manual_layout_preset(self) -> bool:
        """Return True when the selected preset is a saved manual layout."""
        idx = self._selected_preset_index()
        if idx is None:
            return False
        return is_manual_layout_plot(self.project_state.plots[idx])

    def _uses_manual_layout(self) -> bool:
        """Return True when the preview uses the multi-panel manual layout."""
        return self._is_manual_mode() or self._is_manual_layout_preset()

    def _is_mode_preset(self) -> bool:
        """Return True when the selected preset uses ``signals`` + ``mode``."""
        idx = self._selected_preset_index()
        if idx is None:
            return False
        return not is_manual_layout_plot(self.project_state.plots[idx])

    def _sync_manual_controls_enabled(self) -> None:
        """Enable manual plot controls for free manual and layout presets."""
        enabled = self._uses_manual_layout()
        self.manual_plot_count_spin.setEnabled(enabled)
        self.manual_plot_title_edit.setEnabled(enabled)
        can_remove = enabled and self.manual_plot_count_spin.value() > 1
        self.manual_remove_plot_btn.setEnabled(can_remove)
        self.mode_preset_combo.setEnabled(self._is_mode_preset())
        self.subplot_menu_btn.setEnabled(self._is_mode_preset())
        can_save = self.project_controller is not None and (
            self._uses_manual_layout() or self._is_mode_preset()
        )
        self.save_preset_btn.setEnabled(can_save)

    def _save_active_manual_title(self) -> None:
        """Persist the title field into the active manual plot."""
        if not self._manual.selections:
            return
        self._manual.save_title(self._manual.active, self.manual_plot_title_edit.text().strip())

    def _load_active_manual_title(self) -> None:
        """Load the active manual plot title into the title field."""
        if not self._manual.selections:
            self.manual_plot_title_edit.clear()
            return
        self._manual.ensure_titles_aligned()
        idx = min(self._manual.active, len(self._manual.titles) - 1)
        self.manual_plot_title_edit.blockSignals(True)
        self.manual_plot_title_edit.setText(self._manual.titles[idx])
        self.manual_plot_title_edit.blockSignals(False)

    def _on_manual_plot_title_edited(self) -> None:
        """Apply title edit and refresh preview."""
        self._save_active_manual_title()
        self._update_preview_plot()

    def _on_manual_plot_count_changed(self, value: int) -> None:
        """Grow or shrink manual plots; decreasing removes only the last plot."""
        self._save_active_manual_selection()
        self._save_active_manual_title()
        self._manual.resize(value)
        self._manual.clamp_active()
        self._sync_manual_controls_enabled()
        self._load_active_manual_title()
        self._load_manual_selection_to_tree(self._manual.selections[self._manual.active])
        self._refresh_all_tree_style_labels()
        self._update_preview_plot()

    def _on_manual_remove_selected_plot(self) -> None:
        """Remove the plot currently selected for editing."""
        if len(self._manual.selections) <= 1:
            return
        self._save_active_manual_title()
        self._manual.remove_at(self._manual.active)
        new_count = len(self._manual.selections)
        self.manual_plot_count_spin.blockSignals(True)
        self.manual_plot_count_spin.setValue(new_count)
        self.manual_plot_count_spin.blockSignals(False)
        self._manual.clamp_active()
        self._sync_manual_controls_enabled()
        self._load_active_manual_title()
        self._load_manual_selection_to_tree(self._manual.selections[self._manual.active])
        self._refresh_all_tree_style_labels()
        self._update_preview_plot()

    def _select_manual_plot(self, index: int) -> None:
        """Select a manual plot for editing (e.g. after clicking its axis)."""
        if index < 0 or index >= len(self._manual.selections):
            return
        if index == self._manual.active:
            self._refresh_manual_panel_highlights()
            return
        self._save_active_manual_selection()
        self._save_active_manual_title()
        self._manual.active = index
        self._load_active_manual_title()
        self._load_manual_selection_to_tree(self._manual.selections[index])
        self._refresh_manual_panel_highlights()

    def _save_active_manual_selection(self) -> None:
        """Persist the signal tree checks into the active manual plot."""
        if not self._manual.selections:
            return
        idx = min(self._manual.active, len(self._manual.selections) - 1)
        self._manual.active = idx
        self._manual.selections[idx] = self._read_selection_from_signal_tree()

    def _read_selection_from_signal_tree(self) -> dict[str, set[str]]:
        """Return selected component labels per signal from the tree widget."""
        selected: dict[str, set[str]] = {}
        for i in range(self.signal_tree.topLevelItemCount()):
            item = self.signal_tree.topLevelItem(i)
            item_data = item.data(0, Qt.UserRole)
            if (
                isinstance(item_data, tuple)
                and len(item_data) == 3
                and item_data[0] == "component"
            ):
                if item.checkState(0) == Qt.Checked:
                    sig = str(item_data[1])
                    selected.setdefault(sig, set()).add(str(item_data[2]))
                continue
            if not isinstance(item_data, tuple) or len(item_data) < 2:
                continue
            sig = str(item_data[1])
            labels: set[str] = set()
            for c in range(item.childCount()):
                child = item.child(c)
                if child.checkState(0) != Qt.Checked:
                    continue
                child_data = child.data(0, Qt.UserRole)
                if isinstance(child_data, tuple) and len(child_data) == 3:
                    labels.add(str(child_data[2]))
            if labels:
                selected[sig] = labels
        return selected

    def _load_manual_selection_to_tree(self, selection: dict[str, set[str]]) -> None:
        """Apply a manual plot selection to the signal tree checkboxes."""
        self._updating_signal_tree = True
        try:
            for i in range(self.signal_tree.topLevelItemCount()):
                item = self.signal_tree.topLevelItem(i)
                item_data = item.data(0, Qt.UserRole)
                if (
                    isinstance(item_data, tuple)
                    and len(item_data) == 3
                    and item_data[0] == "component"
                ):
                    sig = str(item_data[1])
                    label = str(item_data[2])
                    checked = label in selection.get(sig, set())
                    item.setCheckState(
                        0, Qt.Checked if checked else Qt.Unchecked
                    )
                    continue
                if not isinstance(item_data, tuple) or len(item_data) < 2:
                    continue
                sig = str(item_data[1])
                labels = selection.get(sig, set())
                checked_count = 0
                for c in range(item.childCount()):
                    child = item.child(c)
                    child_data = child.data(0, Qt.UserRole)
                    if not isinstance(child_data, tuple) or len(child_data) != 3:
                        continue
                    label = str(child_data[2])
                    if label in labels:
                        child.setCheckState(0, Qt.Checked)
                        checked_count += 1
                    else:
                        child.setCheckState(0, Qt.Unchecked)
                n_children = item.childCount()
                if checked_count == n_children and n_children > 0:
                    item.setCheckState(0, Qt.Checked)
                else:
                    item.setCheckState(0, Qt.Unchecked)
        finally:
            self._updating_signal_tree = False
        self._refresh_all_tree_style_labels()

    def _on_subplot_toggled(self, _checked: bool):
        """Redraw preview when subplot filters change."""
        self._update_subplot_button_text()
        self._sync_subplot_all_checkbox()
        self._update_preview_plot()

    def _autoscale_preview(self):
        """Autoscale all preview axes."""
        for ax in self.figure.axes:
            ax.relim()
            ax.autoscale_view()
        self.canvas.draw_idle()

    def _on_canvas_click(self, event):
        """Select manual plot on click; double-click toggles enlarged view."""
        if event.inaxes is None:
            return
        key = self._axis_to_panel_key.get(id(event.inaxes))
        if key is None:
            return
        if self._uses_manual_layout() and key.startswith("manual::"):
            try:
                plot_idx = int(key.split("::", 1)[1])
            except ValueError:
                return
            if getattr(event, "dblclick", False):
                self._select_manual_plot(plot_idx)
                if self._focused_panel_key == key:
                    self._focused_panel_key = None
                else:
                    self._focused_panel_key = key
                self._update_preview_plot()
                return
            if self._focused_panel_key is not None:
                self._focused_panel_key = None
                self._update_preview_plot()
            self._select_manual_plot(plot_idx)
            return
        if not getattr(event, "dblclick", False):
            return
        if self._focused_panel_key == key:
            self._focused_panel_key = None
        else:
            self._focused_panel_key = key
        self._update_preview_plot()

    def _populate_plot_presets(self):
        """Populate the plot preset dropdown from project-defined plots."""
        prev_data = self.plot_preset_combo.currentData()
        self.plot_preset_combo.blockSignals(True)
        self.plot_preset_combo.clear()
        self.plot_preset_combo.addItem("Manual selection", None)
        for idx, plot in enumerate(self.project_state.plots):
            title = str(plot.get("title", f"Plot {idx + 1}"))
            self.plot_preset_combo.addItem(title, idx)
        target_idx = self.plot_preset_combo.findData(prev_data)
        if target_idx < 0:
            target_idx = 0
        self.plot_preset_combo.setCurrentIndex(target_idx)
        self.plot_preset_combo.blockSignals(False)
        self._sync_manual_controls_enabled()
        self._sync_subplot_all_checkbox()

    def _selected_preset_index(self) -> int | None:
        """Return selected plot preset index or None for manual mode."""
        data = self.plot_preset_combo.currentData()
        if isinstance(data, int):
            return data
        return None

    def _find_manual_preset_index_by_title(self, title: str) -> int | None:
        """Return index of a manual layout preset with ``title``, or None."""
        key = title.strip()
        if not key:
            return None
        for idx, plot in enumerate(self.project_state.plots):
            if is_manual_layout_plot(plot) and str(plot.get("title", "")).strip() == key:
                return idx
        return None

    def _component_labels_for_signal(self, sig: str) -> list[str]:
        """Return component labels for one signal."""
        return [label for label, _ in series_from_signal(self.project_state.logs, sig)]

    def _update_preview_plot(self):
        """Redraw the embedded preview plot from the selected signals."""
        self.figure.clear()
        preset_index = self._selected_preset_index()
        if self._uses_manual_layout():
            if self._is_manual_mode():
                sel = self._read_selection_from_signal_tree()
                # Avoid wiping panel data when the tree was rebuilt but not restored yet.
                if sel or not (
                    self._manual.selections
                    and self._manual.selections[
                        min(self._manual.active, len(self._manual.selections) - 1)
                    ]
                ):
                    self._save_active_manual_selection()
            self._render_manual_plots_preview()
            self.canvas.draw()
            return

        preset_plot = self.project_state.plots[preset_index]
        active_signals = sorted(self._read_mode_signals_from_tree())

        if not active_signals:
            self._refresh_subplot_filter([], keep_current=False)
            self.canvas.draw()
            return

        time = np.asarray(self.project_state.logs["time"]).flatten()
        T = len(time)

        try:
            series_by_signal: list[tuple[str, list[tuple[str, np.ndarray]]]] = []
            for sig in active_signals:
                sig_series = series_from_signal(self.project_state.logs, sig)
                n_samples = len(sig_series[0][1]) if sig_series else 0
                if n_samples != T:
                    raise ValueError(
                        f"Time length mismatch for '{sig}': time has {T} samples but signal has {n_samples}."
                    )
                series_by_signal.append((sig, sig_series))

            flat_series = flatten_series(series_by_signal)
            mode = self._resolve_defined_mode(
                {"mode": self._current_mode_preset_mode()},
                flat_series,
                series_by_signal,
            )
            panels = self._build_panels_for_mode(mode, series_by_signal, flat_series)
            self._refresh_subplot_filter(panels, keep_current=True)
            enabled_panel_keys = self._selected_subplot_keys()
            panels = [panel for panel in panels if panel[1] in enabled_panel_keys]
            self._render_panels(time, panels, plot=preset_plot)
            self._finalize_layout()

        except Exception as e:
            ax = self.figure.add_subplot(111)
            # Keep the UI responsive; show the error inside the plot area.
            ax.text(
                0.01, 0.99,
                f"Plot preview error:\n{e}",
                transform=ax.transAxes,
                va="top",
                ha="left",
                wrap=True,
            )
            ax.set_axis_off()

        self.canvas.draw()

    def _series_from_manual_selection(
        self, selection: dict[str, set[str]], time: np.ndarray
    ) -> list[tuple[str, np.ndarray]]:
        """Build (label, values) series for one manual plot selection."""
        T = len(time)
        series: list[tuple[str, np.ndarray]] = []
        for sig in sorted(selection.keys()):
            sig_series = series_from_signal(self.project_state.logs, sig)
            n_samples = len(sig_series[0][1]) if sig_series else 0
            if n_samples != T:
                raise ValueError(
                    f"Time length mismatch for '{sig}': time has {T} samples but signal has {n_samples}."
                )
            selected_labels = selection[sig]
            for label, values in sig_series:
                if label in selected_labels:
                    series.append((label, values))
        return series

    def _draw_manual_panel(
        self,
        ax,
        time: np.ndarray,
        title: str,
        key: str,
        series: list[tuple[str, np.ndarray]],
        panel_idx: int,
    ) -> None:
        """Draw one manual plot panel and register it for hit-testing."""
        if series:
            for label, values in series:
                plot_step_series_styled(
                    ax,
                    time,
                    values,
                    label,
                    self._get_manual_series_style(panel_idx, label),
                )
        else:
            ax.text(
                0.5,
                0.5,
                "No signals selected.",
                transform=ax.transAxes,
                ha="center",
                va="center",
            )
        ax.set_title(title)
        self._style_axis(ax)
        self._axis_to_panel_key[id(ax)] = key
        self._highlight_manual_axis(ax, key == f"manual::{self._manual.active}")

    @staticmethod
    def _manual_panel_index_from_key(key: str) -> int:
        """Return manual panel index encoded in a preview panel key."""
        if key.startswith("manual::"):
            try:
                return int(key.split("::", 1)[1])
            except ValueError:
                pass
        return 0

    def _render_manual_plots_preview(self) -> None:
        """Render all manual plot panels in a 2-column grid (last odd spans full width)."""
        self._refresh_subplot_filter([], keep_current=False)
        self._axis_to_panel_key.clear()

        n_plots = len(self._manual.selections)
        if n_plots == 0:
            return

        time = np.asarray(self.project_state.logs["time"]).flatten()
        panels: list[tuple[str, str, list[tuple[str, np.ndarray]]]] = []
        try:
            for i, selection in enumerate(self._manual.selections):
                series = self._series_from_manual_selection(selection, time)
                title = self._manual.plot_title(i)
                panels.append((title, f"manual::{i}", series))
        except Exception as e:
            ax = self.figure.add_subplot(111)
            ax.text(
                0.01,
                0.99,
                f"Plot preview error:\n{e}",
                transform=ax.transAxes,
                va="top",
                ha="left",
                wrap=True,
            )
            ax.set_axis_off()
            return

        if self._focused_panel_key is not None:
            existing_keys = {key for _, key, _ in panels}
            if self._focused_panel_key in existing_keys:
                panels = [p for p in panels if p[1] == self._focused_panel_key]
            else:
                self._focused_panel_key = None

        if len(panels) == 1:
            title, key, series = panels[0]
            ax = self.figure.add_subplot(111)
            panel_idx = self._manual_panel_index_from_key(key)
            self._draw_manual_panel(ax, time, title, key, series, panel_idx)
            self._finalize_layout()
            return

        n_rows = (n_plots + 1) // 2
        gs = gridspec.GridSpec(n_rows, 2, figure=self.figure)
        for i, (title, key, series) in enumerate(panels):
            if i == n_plots - 1 and n_plots % 2 == 1:
                ax = self.figure.add_subplot(gs[i // 2, :])
            else:
                ax = self.figure.add_subplot(gs[i // 2, i % 2])
            panel_idx = self._manual_panel_index_from_key(key)
            self._draw_manual_panel(ax, time, title, key, series, panel_idx)
        self._finalize_layout()

    def _highlight_manual_axis(self, ax, selected: bool) -> None:
        """Visually mark the manual plot currently being edited."""
        width = 2.5 if selected else 0.8
        color = "#1f77b4" if selected else "0.8"
        for spine in ax.spines.values():
            spine.set_linewidth(width)
            spine.set_edgecolor(color)

    def _refresh_manual_panel_highlights(self) -> None:
        """Update active-panel borders without redrawing plot data (keeps zoom)."""
        if not self._uses_manual_layout() or not self.figure.axes:
            return
        active_key = f"manual::{self._manual.active}"
        for ax in self.figure.axes:
            key = self._axis_to_panel_key.get(id(ax))
            if key is None or not key.startswith("manual::"):
                continue
            self._highlight_manual_axis(ax, key == active_key)
        self.canvas.draw_idle()

    def _refresh_subplot_filter(self, panels: list[tuple[str, str, list[tuple[str, np.ndarray]]]], keep_current: bool):
        """Rebuild subplot check-list from panel descriptors."""
        current_enabled = self._selected_subplot_keys() if keep_current else set()
        new_items = [(title, key) for title, key, _ in panels]
        if new_items == self._subplot_items and keep_current:
            return

        self._subplot_items = new_items
        self._subplot_actions.clear()
        self.subplot_menu.clear()
        for title, key in new_items:
            checked = (key in current_enabled) if keep_current else True
            action = self.subplot_menu.addAction(title)
            action.setCheckable(True)
            action.setChecked(checked)
            action.toggled.connect(self._on_subplot_toggled)
            self._subplot_actions[key] = action
        self._update_subplot_button_text()
        self._sync_subplot_all_checkbox()

    def _on_subplot_all_cb_changed(self, *_args: object) -> None:
        """Apply or clear all subplot menu checks from the All checkbox."""
        if not self._subplot_actions:
            return
        check_all = self.subplot_all_cb.isChecked()
        for action in self._subplot_actions.values():
            action.blockSignals(True)
            action.setChecked(check_all)
            action.blockSignals(False)
        self._update_subplot_button_text()
        self._update_preview_plot()

    def _sync_subplot_all_checkbox(self) -> None:
        """Enable the All checkbox and mirror whether every subplot action is checked."""
        self.subplot_all_cb.blockSignals(True)
        try:
            enabled = self.subplot_menu_btn.isEnabled() and len(self._subplot_actions) > 0
            self.subplot_all_cb.setEnabled(enabled)
            if not enabled or not self._subplot_actions:
                self.subplot_all_cb.setChecked(False)
            else:
                all_on = all(action.isChecked() for action in self._subplot_actions.values())
                self.subplot_all_cb.setChecked(all_on)
        finally:
            self.subplot_all_cb.blockSignals(False)

    def _selected_subplot_keys(self) -> set[str]:
        """Return selected subplot panel keys."""
        if not self._subplot_actions:
            return set()
        keys: set[str] = set()
        for key, action in self._subplot_actions.items():
            if action.isChecked():
                if isinstance(key, str):
                    keys.add(key)
        return keys

    def _update_subplot_button_text(self) -> None:
        """Update dropdown button label with current selection count."""
        total = len(self._subplot_actions)
        if total == 0:
            self.subplot_menu_btn.setText("Select subplots")
            return
        selected = len(self._selected_subplot_keys())
        self.subplot_menu_btn.setText(f"Subplots: {selected}/{total}")

    def _resolve_defined_mode(
        self,
        plot: dict,
        flat_series: list[tuple[str, str, np.ndarray]],
        series_by_signal: list[tuple[str, list[tuple[str, np.ndarray]]]],
    ) -> str:
        """Resolve mode for a predefined plot using same defaults as project plots."""
        mode = str(plot.get("mode", "auto")).strip().lower()
        if mode in {"overlay", "split_signals", "split_components"}:
            return mode
        if mode != "auto":
            return "overlay"
        if len(flat_series) > 6:
            return "split_components"
        if len(series_by_signal) > 2:
            return "split_signals"
        return "overlay"

    def _build_panels_for_mode(
        self,
        mode: str,
        series_by_signal: list[tuple[str, list[tuple[str, np.ndarray]]]],
        flat_series: list[tuple[str, str, np.ndarray]],
    ) -> list[tuple[str, str, list[tuple[str, np.ndarray]]]]:
        """Build panel descriptors: (title, key, series list)."""
        if mode == "overlay":
            panel_series = [(label, values) for _, label, values in flat_series]
            return [("Overlay", "overlay::all", panel_series)]

        if mode == "split_signals":
            panels = []
            for sig, sig_series in series_by_signal:
                panels.append((sig, f"sig::{sig}", sig_series))
            return panels

        panels = []
        for _, label, values in flat_series:
            panels.append((label, f"cmp::{label}", [(label, values)]))
        return panels

    def _load_manual_state_from_layout_plot(self, plot: dict) -> None:
        """Restore manual panels, titles, and styles from a layout preset."""
        self._manual.load_from_preset(plot)
        self.manual_plot_count_spin.blockSignals(True)
        self.manual_plot_count_spin.setValue(len(self._manual.selections))
        self.manual_plot_count_spin.blockSignals(False)
        self._manual.clamp_active()
        self._load_active_manual_title()
        self._load_manual_selection_to_tree(self._manual.selections[self._manual.active])

    def _flush_active_preset_working(self) -> None:
        """Persist in-memory edits for the active preset before rebuilding the UI."""
        idx = self._selected_preset_index()
        if idx is None:
            return
        if is_manual_layout_plot(self.project_state.plots[idx]):
            self._save_active_manual_selection()
            self._save_active_manual_title()
        else:
            self._store_mode_preset_working(idx)

    def _current_mode_preset_mode(self) -> str:
        data = self.mode_preset_combo.currentData()
        if isinstance(data, str):
            return data
        return "auto"

    def _set_mode_preset_combo(self, mode: str) -> None:
        idx = self.mode_preset_combo.findData(mode)
        if idx < 0:
            idx = self.mode_preset_combo.findData("auto")
        if idx < 0:
            idx = 0
        self.mode_preset_combo.blockSignals(True)
        self.mode_preset_combo.setCurrentIndex(idx)
        self.mode_preset_combo.blockSignals(False)

    def _read_mode_signals_from_tree(self) -> list[str]:
        """Return top-level signal names checked for a mode-based preset."""
        selected: list[str] = []
        for i in range(self.signal_tree.topLevelItemCount()):
            item = self.signal_tree.topLevelItem(i)
            data = item.data(0, Qt.UserRole)
            if not isinstance(data, tuple) or len(data) < 2:
                continue
            if data[0] == "signal" and item.checkState(0) == Qt.Checked:
                selected.append(str(data[1]))
            elif data[0] == "component" and item.checkState(0) == Qt.Checked:
                selected.append(str(data[1]))
        return sorted(set(selected))

    def _load_mode_signals_to_tree(self, signals: set[str]) -> None:
        """Apply mode-preset signal selection to the signal tree."""
        self._updating_signal_tree = True
        try:
            for i in range(self.signal_tree.topLevelItemCount()):
                item = self.signal_tree.topLevelItem(i)
                data = item.data(0, Qt.UserRole)
                if isinstance(data, tuple) and len(data) == 3 and data[0] == "component":
                    sig = str(data[1])
                    checked = sig in signals
                    item.setCheckState(0, Qt.Checked if checked else Qt.Unchecked)
                    continue
                if not isinstance(data, tuple) or len(data) < 2 or data[0] != "signal":
                    continue
                sig = str(data[1])
                checked_count = 0
                for c in range(item.childCount()):
                    child = item.child(c)
                    child_data = child.data(0, Qt.UserRole)
                    if not isinstance(child_data, tuple) or len(child_data) != 3:
                        continue
                    if sig in signals:
                        child.setCheckState(0, Qt.Checked)
                        checked_count += 1
                    else:
                        child.setCheckState(0, Qt.Unchecked)
                n_children = item.childCount()
                if n_children > 0:
                    if checked_count == n_children and n_children > 0:
                        item.setCheckState(0, Qt.Checked)
                    else:
                        item.setCheckState(0, Qt.Unchecked)
                else:
                    item.setCheckState(0, Qt.Checked if sig in signals else Qt.Unchecked)
        finally:
            self._updating_signal_tree = False

    def _store_mode_preset_working(self, idx: int) -> None:
        self._mode.store(idx, self._read_mode_signals_from_tree(), self._current_mode_preset_mode())

    def _load_mode_preset(self, idx: int) -> None:
        """Restore a mode preset from session cache or project YAML."""
        cached = self._mode.get_cached(idx)
        if isinstance(cached, dict):
            signals = [str(s) for s in cached.get("signals", []) if s]
            mode = str(cached.get("mode", "auto"))
            raw_styles = cached.get("styles", {})
            self._mode.styles = copy.deepcopy(raw_styles) if isinstance(raw_styles, dict) else {}
        else:
            plot = self.project_state.plots[idx]
            signals = [str(s) for s in plot.get("signals", []) if s]
            mode = str(plot.get("mode", "auto"))
            self._mode.styles = _ModePresetSession.styles_from_plot(plot)
        self._set_mode_preset_combo(mode)
        self._load_mode_signals_to_tree(set(signals))

    def _save_plot_preset(self) -> None:
        """Save the active manual or mode-based plot preset."""
        if self.project_controller is None:
            return
        if self._uses_manual_layout():
            self._save_manual_as_plot_preset()
        elif self._is_mode_preset():
            self._save_mode_as_plot_preset()

    def _save_mode_as_plot_preset(self) -> None:
        """Write the edited mode-based preset into the project."""
        idx = self._selected_preset_index()
        if idx is None or self.project_controller is None:
            return
        self._store_mode_preset_working(idx)
        cached = self._mode.get_cached(idx) or {}
        signals = list(cached.get("signals", []))
        if not signals:
            QMessageBox.warning(
                self,
                "Nothing to save",
                "No signal selected.\nCheck at least one signal.",
            )
            return
        mode = str(cached.get("mode", "auto"))
        title = str(self.project_state.plots[idx].get("title", "Plot"))
        self.project_controller.update_plot(
            idx,
            title,
            signals,
            mode=mode,
            series_styles=self._mode.serialize_styles(),
        )
        QMessageBox.information(
            self,
            "Plot preset saved",
            f"Preset « {title} » updated.\n"
            "Save the project (Ctrl+S) to write it to project.yaml.",
        )

    def _save_manual_as_plot_preset(self) -> None:
        """Save or overwrite a manual layout plot preset."""
        if self.project_controller is None or not self._uses_manual_layout():
            return

        self._save_active_manual_selection()
        self._save_active_manual_title()
        self._manual.ensure_titles_aligned()

        editing_idx = (
            self._selected_preset_index() if self._is_manual_layout_preset() else None
        )
        if editing_idx is not None:
            preset_name = str(
                self.project_state.plots[editing_idx].get("title", "Manual layout")
            ).strip() or "Manual layout"
        else:
            default_name = (
                self._manual.plot_title(0) if self._manual.titles else "Manual layout"
            )
            name, ok = QInputDialog.getText(
                self,
                "Save plot preset",
                "Preset name:",
                text=default_name,
            )
            if not ok or not name.strip():
                return
            preset_name = name.strip()
        plot_dict = manual_layout_to_plot_dict(
            preset_name,
            self._manual.titles,
            self._manual.selections,
            self._manual.panel_styles,
        )
        if plot_dict is None:
            QMessageBox.warning(
                self,
                "Nothing to save",
                "No plot panel has any signal selected.\n"
                "Check signals for at least one panel.",
            )
            return

        target_idx = editing_idx
        if target_idx is None:
            target_idx = self._find_manual_preset_index_by_title(preset_name)

        created = target_idx is None
        if target_idx is None:
            target_idx = self.project_controller.add_manual_layout_preset(plot_dict)
        else:
            self.project_controller.update_manual_layout_preset(target_idx, plot_dict)

        self._populate_plot_presets()
        combo_idx = self.plot_preset_combo.findData(target_idx)
        self.plot_preset_combo.blockSignals(True)
        if combo_idx >= 0:
            self.plot_preset_combo.setCurrentIndex(combo_idx)
        self.plot_preset_combo.blockSignals(False)
        self._on_plot_preset_changed(self.plot_preset_combo.currentIndex())

        action = "added" if created else "updated"
        QMessageBox.information(
            self,
            "Plot preset saved",
            f"Preset « {preset_name} » {action} "
            f"({len(plot_dict.get('panels', []))} panels).\n"
            "Save the project (Ctrl+S) to write it to project.yaml.",
        )

    def _render_panels(
        self,
        time: np.ndarray,
        panels: list[tuple[str, str, list[tuple[str, np.ndarray]]]],
        plot: dict | None = None,
    ) -> None:
        """Render selected panels on one or multiple subplots."""
        self._axis_to_panel_key.clear()
        if self._focused_panel_key is not None:
            existing_keys = {key for _, key, _ in panels}
            if self._focused_panel_key in existing_keys:
                panels = [p for p in panels if p[1] == self._focused_panel_key]
            else:
                self._focused_panel_key = None

        if not panels:
            ax = self.figure.add_subplot(111)
            ax.text(
                0.01,
                0.99,
                "No subplot selected.",
                transform=ax.transAxes,
                va="top",
                ha="left",
            )
            ax.set_axis_off()
            return

        if len(panels) == 1:
            ax = self.figure.add_subplot(111)
            title, key, series = panels[0]
            for label, values in series:
                plot_step_series_styled(ax, time, values, label, self._get_series_style(label, plot))
            ax.set_title(title)
            self._style_axis(ax)
            self._axis_to_panel_key[id(ax)] = key
            return

        rows, cols = self._panel_grid_shape(len(panels))
        share_x = cols == 1
        axes_grid = self.figure.subplots(rows, cols, sharex=share_x, squeeze=False)
        axes = axes_grid.flatten()
        for i, (title, key, series) in enumerate(panels):
            ax = axes[i]
            for label, values in series:
                plot_step_series_styled(ax, time, values, label, self._get_series_style(label, plot))
            ax.set_title(title)
            self._style_axis(ax)
            self._axis_to_panel_key[id(ax)] = key

        # Hide unused cells when panel count does not fill the grid.
        for j in range(len(panels), len(axes)):
            axes[j].set_axis_off()

    def _style_axis(self, ax) -> None:
        """Apply user-selected axis style."""
        ax.set_xlabel("Time [s]")
        ax.grid(self.grid_cb.isChecked())
        if self.legend_cb.isChecked() and ax.lines:
            ax.legend()

    def _finalize_layout(self) -> None:
        """Apply a robust layout for many stacked axes."""
        n_axes = len(self.figure.axes)
        if n_axes >= 8:
            self.figure.subplots_adjust(hspace=0.75)
            return
        self.figure.tight_layout()

    def _panel_grid_shape(self, n_panels: int) -> tuple[int, int]:
        """Return (rows, cols) layout for panel rendering."""
        if n_panels <= 1:
            return 1, 1
        if n_panels == 2:
            return 2, 1
        if n_panels == 3:
            return 3, 1
        if n_panels == 4:
            return 2, 2
        rows = int(np.ceil(n_panels / 2))
        return rows, 2

    def _plot_defined_plots(self):
        """Open standalone matplotlib windows for the configured plots."""
        if not self.project_state.plots:
            QMessageBox.information(
                self,
                "No plots defined",
                "No plots are defined in the project settings."
            )
            return

        plot_from_config(
            logs=self.project_state.logs,
            plot_cfg=PlotConfig(self.project_state.plots),
            show=True,
            block=False
        )
