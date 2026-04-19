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

from PySide6.QtWidgets import QComboBox, QFormLayout, QLabel, QLineEdit

from pySimBlocks.gui.blocks.block_dialog_session import BlockDialogSession
from pySimBlocks.gui.blocks.block_meta import BlockMeta
from pySimBlocks.gui.blocks.parameter_meta import ParameterMeta
from pySimBlocks.gui.blocks.port_meta import PortMeta


class BusFromMeta(BlockMeta):
    """Describe the GUI metadata of the BusFrom interface block.

    The ``tag`` parameter is rendered as a dropdown populated with all tags
    currently declared by Goto blocks in the same diagram.  If no Goto block
    is present (e.g. outside the full GUI context), the field falls back to
    a plain text edit so the user can still type a tag manually.
    """

    def __init__(self):
        """Initialize BusFrom block metadata.

        Args:
            None.

        Raises:
            None.
        """
        self.name = "BusFrom"
        self.category = "interfaces"
        self.type = "bus_from"
        self.summary = "Read a signal from the virtual signal bus by tag."
        self.description = (
            "Reads the value published by the matching **Goto** block each tick.\n\n"
            "The **tag** dropdown lists all tags currently declared by Goto blocks\n"
            "in the diagram. No explicit wire connection is needed between Goto\n"
            "and BusFrom: the signal bus handles routing automatically.\n\n"
            "The topological sort guarantees that the matching Goto executes\n"
            "before this block within the same simulation step."
        )

        self.parameters = [
            ParameterMeta(
                name="tag",
                type="str",
                required=True,
                description=(
                    "Signal bus tag. Must match the tag of the corresponding "
                    "Goto block."
                ),
            ),
            ParameterMeta(
                name="sample_time",
                type="float",
            ),
        ]

        self.outputs = [
            PortMeta(
                name="out",
                display_as="out",
                shape=["n", 1],
                description="Signal read from the bus.",
            )
        ]

    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------

    def build_param(
        self,
        session: BlockDialogSession,
        form: QFormLayout,
        readonly: bool = False,
    ) -> None:
        """Build parameter widgets, replacing the tag field with a dropdown.

        When a project state is available, the ``tag`` parameter is rendered
        as a ``QComboBox`` populated with every tag currently declared by a
        Goto block in the diagram.  An extra ``(free text)`` entry lets the
        user type an arbitrary tag when the desired Goto does not exist yet.
        If no project state is available the tag falls back to a plain
        ``QLineEdit``.

        All other parameters use the standard widget builder from the base
        class.

        Args:
            session: Active dialog session.
            form: Form layout receiving the widgets.
            readonly: Whether the dialog is read-only.
        """
        # Block name row (standard)
        name_edit = QLineEdit(session.instance.name)
        name_edit.textChanged.connect(
            lambda val: self._on_param_changed(val, "name", session, readonly)
        )
        if readonly:
            name_edit.setReadOnly(True)
        form.addRow(QLabel("Block name:"), name_edit)
        session.name_edit = name_edit

        # Parameter rows
        for param_meta in self.parameters:
            if param_meta.name == "tag":
                label, widget = self._build_tag_row(session, param_meta, readonly)
            else:
                label, widget = self._create_param_row(session, param_meta, readonly)
                if widget is None:
                    continue

            if readonly:
                self._set_readonly_style(widget)

            form.addRow(label, widget)
            session.param_widgets[param_meta.name] = widget
            session.param_labels[param_meta.name] = label

    # --------------------------------------------------------------------------
    # Private methods
    # --------------------------------------------------------------------------

    def _collect_goto_tags(self, session: BlockDialogSession) -> list[str]:
        """Return all tag values declared by Goto blocks in the project.

        Args:
            session: Active dialog session with an optional project_state.

        Returns:
            Sorted list of unique tag strings found in Goto blocks.
            Empty list when project state is unavailable.
        """
        project_state = session.project_state
        if project_state is None:
            return []

        tags: list[str] = []
        for block in project_state.blocks:
            if block.meta.type == "goto":
                tag = block.parameters.get("tag")
                if tag and isinstance(tag, str) and tag not in tags:
                    tags.append(tag)

        return sorted(tags)

    def _build_tag_row(
        self,
        session: BlockDialogSession,
        param_meta: ParameterMeta,
        readonly: bool,
    ) -> tuple[QLabel, QComboBox | QLineEdit]:
        """Build the tag parameter row as a dropdown or a plain text edit.

        A ``QComboBox`` is used when at least one Goto tag is available in
        the project.  A sentinel entry ``(free text)`` is appended so the
        user can still enter a tag that does not correspond to any existing
        Goto block.  When the sentinel is selected the combo is replaced by
        a ``QLineEdit``.

        If no Goto tags are found, a plain ``QLineEdit`` is used directly.

        Args:
            session: Active dialog session.
            param_meta: Metadata for the ``tag`` parameter.
            readonly: Whether the widget should be read-only.

        Returns:
            ``(label, widget)`` pair for the tag parameter row.
        """
        label = QLabel(f"{param_meta.name}:")
        if param_meta.description:
            label.setToolTip(param_meta.description)

        goto_tags = self._collect_goto_tags(session)
        current_value = session.local_params.get("tag") or ""

        if not goto_tags:
            # No Goto tags available — plain text edit
            widget = QLineEdit()
            widget.setText(str(current_value))
            widget.textChanged.connect(
                lambda val: self._on_param_changed(val, "tag", session, readonly)
            )
            return label, widget

        # Build combo with all known tags plus a free-text sentinel
        _FREE_TEXT = "(free text)"
        combo = QComboBox()
        for tag in goto_tags:
            combo.addItem(tag)
        combo.addItem(_FREE_TEXT)

        # Pre-select the current value if it is in the list
        if current_value in goto_tags:
            combo.setCurrentText(current_value)
        else:
            combo.setCurrentText(_FREE_TEXT)

        def _on_combo_changed(text: str) -> None:
            if text == _FREE_TEXT:
                return
            self._on_param_changed(text, "tag", session, readonly)

        combo.currentTextChanged.connect(_on_combo_changed)
        # Propagate the initial selection immediately
        if combo.currentText() != _FREE_TEXT:
            self._on_param_changed(combo.currentText(), "tag", session, readonly)

        return label, combo
