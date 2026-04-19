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

import ast
import os
from abc import ABC
from pathlib import Path
from typing import Any, Dict, Literal, Sequence

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from pySimBlocks.gui.blocks.block_dialog_session import BlockDialogSession
from pySimBlocks.gui.blocks.parameter_meta import ParameterMeta
from pySimBlocks.gui.blocks.port_meta import PortMeta
from pySimBlocks.gui.models import BlockInstance, PortInstance


class BlockMeta(ABC):
    """Define the GUI metadata contract for one block type.

    Subclasses declare static block metadata, optional dialog customizations,
    and dynamic port-resolution rules used by the GUI layer.
    """


    # ----------- Mandatory class attributes (must be overridden) -----------
    #: User-facing block name.
    name: str
    #: GUI block category.
    category: str
    #: Stable block type identifier.
    type: str
    #: Short summary displayed in the GUI.
    summary: str
    #: Rich description displayed in the dialog.
    description: str

    # ----------- Optional declarations -----------
    #: Optional documentation file path, relative to the project directory.
    doc_path: Path | None = None
    #: Declared block parameters.
    parameters: Sequence[ParameterMeta] = ()
    #: Declared input port metadata.
    inputs: Sequence[PortMeta] = ()
    #: Declared output port metadata.
    outputs: Sequence[PortMeta] = ()

    # --------------------------------------------------------------------------
    # Public Methods
    # --------------------------------------------------------------------------

    def create_dialog_session(
        self,
        instance: BlockInstance,
        project_dir: Path | None = None,
        project_state=None,
    ) -> BlockDialogSession:
        """Create a dialog session for a block instance.

        Args:
            instance: Block instance being edited.
            project_dir: Project directory used to resolve relative files.
            project_state: Full project state for blocks that need to
                inspect other blocks in the diagram. None outside the GUI.

        Returns:
            New dialog session object bound to the instance.
        """
        return BlockDialogSession(self, instance, project_dir, project_state)

    def is_parameter_active(self, 
                            param_name: str, 
                            instance_params: Dict[str, Any]) -> bool:
        """Return whether a parameter should be visible for an instance.

        Args:
            param_name: Parameter name to test.
            instance_params: Current instance parameter values.

        Returns:
            True when the parameter is active.
        """
        return True

    def gather_params(self, session: BlockDialogSession) -> dict[str, Any]:
        """Collect dialog parameters into a serialized parameter mapping.

        Args:
            session: Active dialog session.

        Returns:
            Parameter mapping gathered from the dialog state.
        """
        # Keep full local state, including inactive params, so values are cached
        # across visibility toggles and dialog reopen.
        return session.local_params.copy()

    def resolve_port_group(self, 
                           port_meta: PortMeta,
                           direction: Literal['input', 'output'], 
                           instance: "BlockInstance"
    ) -> list["PortInstance"]:
        """Resolve one declared port group into concrete port instances.

        Args:
            port_meta: Declared port metadata.
            direction: Direction of the port group.
            instance: Block instance whose ports are being built.

        Returns:
            Concrete port instances for the given port group.
        """
        return [PortInstance(port_meta.name, port_meta.display_as, direction, instance)]
    
    def build_ports(self, instance: "BlockInstance") -> list["PortInstance"]:
        """Build all concrete ports for a block instance.

        Args:
            instance: Block instance whose ports are being built.

        Returns:
            Ordered list of resolved input and output ports.
        """
        ports = []

        for pmeta in self.inputs:
            ports.extend(self.resolve_port_group(pmeta, "input", instance))

        for pmeta in self.outputs:
            ports.extend(self.resolve_port_group(pmeta, "output", instance))

        return ports

    def build_description(self, form: QFormLayout):
        """Build the default block description section in the dialog.

        Args:
            form: Form layout receiving the description widgets.
        """
        title = QLabel(f"<b>{self.name}</b>")
        title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        form.addRow(title)

        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setFrameShadow(QFrame.Raised)
        frame.setLineWidth(1)

        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(8, 6, 8, 6)

        desc = QTextBrowser()
        desc.setMarkdown(self.description)
        desc.setReadOnly(True)
        desc.setFrameShape(QFrame.NoFrame)
        desc.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        desc.document().setTextWidth(400)
        desc.setFixedHeight(int(desc.document().size().height()) + 6)

        frame_layout.addWidget(desc)
        form.addRow(frame)

    def build_pre_param(self, 
                        session: BlockDialogSession,
                        form: QFormLayout, 
                        readonly: bool = False):
        """Build widgets shown before the standard parameter rows.

        Args:
            session: Active dialog session.
            form: Form layout receiving the widgets.
            readonly: Whether the dialog is read-only.
        """
        pass

    def build_param(self, 
                    session: BlockDialogSession,
                    form: QFormLayout, 
                    readonly: bool = False):
        """Build the standard parameter widgets for the dialog.

        Args:
            session: Active dialog session.
            form: Form layout receiving the widgets.
            readonly: Whether the dialog is read-only.
        """


        # --- Block name ---
        name_edit = QLineEdit(session.instance.name)
        name_edit.textChanged.connect(
            lambda val: self._on_param_changed(val, "name", session, readonly)
        )
        form.addRow(QLabel("Block name:"), name_edit)
        if readonly:
            name_edit.setReadOnly(True)
        session.name_edit = name_edit

        # --- Parameters ---
        for param_meta in self.parameters:
            param_name = param_meta.name

            label, widget = self._create_param_row(session, param_meta, readonly)
            if widget is None:
                continue
            if readonly:
                self._set_readonly_style(widget) 

            form.addRow(label, widget)

            session.param_widgets[param_name] = widget
            session.param_labels[param_name] = label

    def build_post_param(self, 
                         session: BlockDialogSession,
                         form: QFormLayout, 
                         readonly: bool = False):
        """Build widgets shown after the standard parameter rows.

        Args:
            session: Active dialog session.
            form: Form layout receiving the widgets.
            readonly: Whether the dialog is read-only.
        """
        pass

    def build_file_param_row(
        self,
        session: BlockDialogSession,
        form: QFormLayout,
        pmeta: ParameterMeta,
        readonly: bool = False,
        file_filter: str = "Python files (*.py);;All files (*)",
    ) -> None:
        """Build a parameter row with a file picker button.

        Args:
            session: Active dialog session.
            form: Form layout receiving the widgets.
            pmeta: Metadata of the file parameter.
            readonly: Whether the dialog is read-only.
            file_filter: File picker filter string.
        """
        edit = self._create_edit_widget(session, pmeta, readonly)
        if readonly:
            self._set_readonly_style(edit)

        browse_btn = QPushButton("...")
        browse_btn.setToolTip("Select file from disk")
        browse_btn.setEnabled(not readonly)
        browse_btn.clicked.connect(
            lambda: self._browse_and_set_relative_file(edit, session.project_dir, file_filter)
        )

        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.addWidget(edit)
        row_layout.addWidget(browse_btn)

        label = QLabel(f"{pmeta.name}:")
        if pmeta.description:
            label.setToolTip(pmeta.description)

        form.addRow(label, row_widget)
        session.param_widgets[pmeta.name] = row_widget
        session.param_labels[pmeta.name] = label

    def refresh_form(self, session: BlockDialogSession):
        """Refresh widget visibility from the current local parameter state.

        Args:
            session: Active dialog session.
        """

        for param_name, widget in session.param_widgets.items():
            label = session.param_labels[param_name]

            active = self.is_parameter_active(param_name, session.local_params)

            widget.setVisible(active)
            label.setVisible(active)


    # --------------------------------------------------------------------------
    # Private Methods
    # --------------------------------------------------------------------------
    def _create_param_row(self, 
                             session: BlockDialogSession,
                             pmeta: ParameterMeta, 
                             readonly: bool = False
                             ) -> tuple[QLabel, QWidget]:
        """Create the label and widget for one parameter row."""

        # ENUM
        if pmeta.type == "enum":
            widget = self._create_enum_widget(session, pmeta, readonly)
        
        else: # Default: text edit
            widget = self._create_edit_widget(session, pmeta, readonly)

        label = QLabel(f"{pmeta.name}:")
        if pmeta.description:
            label.setToolTip(pmeta.description)

        return label, widget

    def _create_edit_widget(self,
                            session: BlockDialogSession,
                            pmeta: ParameterMeta,
                            readonly: bool = False) -> QLineEdit:
        """Create a line edit widget for one parameter."""
        edit = QLineEdit()
        value = session.local_params.get(pmeta.name)
        if value is not None:
            edit.setText(str(value))
        elif pmeta.default is not None:
            edit.setText(str(pmeta.default))
        edit.textChanged.connect(
            lambda val: self._on_param_changed(val, pmeta.name, session, readonly)
        )
        return edit

    def _create_enum_widget(self,
                            session: BlockDialogSession,
                            pmeta: ParameterMeta,
                            readonly: bool = False) -> QComboBox:
        """Create a combo box widget for one enum parameter."""
        combo = QComboBox()
        for v in pmeta.enum:
            combo.addItem(str(v), userData=v)
        value = session.local_params.get(pmeta.name)
        if value is not None:
            combo.setCurrentText(str(value))
        combo.currentTextChanged.connect(
            lambda val: self._on_param_changed(val, pmeta.name, session, readonly)
        )
        return combo

    def _browse_and_set_relative_file(
        self,
        edit: QLineEdit,
        project_dir: Path | None,
        file_filter: str,
    ) -> None:
        """Open a file picker and write back a relative path when possible."""
        if project_dir is None:
            return

        base_dir = project_dir.expanduser()
        start_dir = base_dir if base_dir.is_dir() else Path.cwd()

        selected_file, _ = QFileDialog.getOpenFileName(
            edit,
            "Select file",
            str(start_dir),
            file_filter,
        )
        if not selected_file:
            return

        selected_path = Path(selected_file).resolve()
        base_resolved = base_dir.resolve()
        try:
            relative_path = selected_path.relative_to(base_resolved)
        except ValueError:
            try:
                relative_path = Path(os.path.relpath(str(selected_path), str(base_resolved)))
            except ValueError:
                # Windows cross-drive case (e.g. C: -> D:): keep absolute path.
                relative_path = selected_path

        edit.setText(relative_path.as_posix())

    def _on_param_changed( self, val: str, name: str, session: BlockDialogSession, readonly: bool,):
        """Update local dialog state after a parameter widget changes."""
        if readonly:
            return

        if name == "name":
            session.local_params["name"] = val
        else:
            text = str(val).strip()
            try:
                session.local_params[name] = ast.literal_eval(text)
            except (ValueError, SyntaxError):
                session.local_params[name] = text
        self.refresh_form(session)

    def _set_readonly_style(self, widget: QWidget):
        """Apply a read-only visual style to supported widgets."""
        if isinstance(widget, QLineEdit):
            widget.setReadOnly(True)
            widget.setStyleSheet("""
                QLineEdit {
                    background-color: #2b2b2b;
                    color: #888888;
                    border: 1px solid #444444;
                }
            """)
        elif isinstance(widget, QComboBox):
            widget.setEnabled(False)
