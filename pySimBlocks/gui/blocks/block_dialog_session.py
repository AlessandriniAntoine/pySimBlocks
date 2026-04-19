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
from typing import TYPE_CHECKING, Any

from PySide6.QtWidgets import QLineEdit

from pySimBlocks.gui.models.block_instance import BlockInstance

if TYPE_CHECKING:
    from pySimBlocks.gui.blocks.block_meta import BlockMeta
    from pySimBlocks.gui.models.project_state import ProjectState


class BlockDialogSession:
    """Store transient dialog state while editing a block instance.

    Attributes:
        meta: Block metadata driving the dialog.
        instance: Block instance being edited.
        project_dir: Project directory used to resolve relative files.
        project_state: Full project state, available when opening from the GUI.
        local_params: Local parameter cache for the open dialog.
        param_widgets: Widgets keyed by parameter name.
        param_labels: Labels keyed by parameter name.
        name_edit: Optional line edit used for the block name.
    """

    def __init__(
        self,
        meta: "BlockMeta",
        instance: BlockInstance,
        project_dir: Path | None = None,
        project_state: "ProjectState | None" = None,
    ):
        """Initialize a block dialog session.

        Args:
            meta: Block metadata driving the dialog.
            instance: Block instance being edited.
            project_dir: Project directory used to resolve relative files.
            project_state: Full project state, used by blocks that need to
                inspect other blocks in the diagram (e.g. From reads Goto
                tags). None when the session is created outside the GUI.

        Raises:
            None.
        """
        self.meta = meta
        self.instance = instance
        self.project_dir = project_dir
        self.project_state: "ProjectState | None" = project_state

        # --- STATE UI (par dialog) ---
        self.local_params: dict[str, Any] = dict(instance.parameters)
        self.param_widgets: dict[str, Any] = {}
        self.param_labels: dict[str, Any] = {}
        self.name_edit: QLineEdit | None = None
