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

import copy
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

from PySide6.QtCore import QObject, Signal, QPointF, QRectF

from pySimBlocks.gui.models import (
    BlockInstance,
    BoundaryPort,
    ConnectionInstance,
    PortInstance,
    ProjectState,
    VisualGroup,
)
from pySimBlocks.gui.diagram_clipboard import (
    DiagramClipboard,
    capture_selection_clipboard,
    clipboard_has_content,
    paste_clipboard,
    undo_paste,
)
from pySimBlocks.gui.group_boundary_labels import (
    boundary_port_label,
    manual_boundary_display_label,
)
from pySimBlocks.gui.services.group_boundary_service import (
    BoundaryWiringState,
    apply_wiring_state,
    can_complete,
    capture_wiring_state,
    connection_endpoints,
    find_connection_for_boundary,
    find_port,
    is_complete,
    port_key,
    validate_external_link,
    validate_internal_link,
)
from pySimBlocks.gui.widgets.diagram_view import DiagramView
from pySimBlocks.gui.blocks.block_meta import BlockMeta
from pySimBlocks.gui.services.yaml_tools import cleanup_runtime_project_yaml
from pySimBlocks.gui.undo_redo.undo_redo_manager import UndoManager
from pySimBlocks.gui.undo_redo.commands import (
    AddBlockCommand,
    AddConnectionCommand,
    AddManualBoundaryCommand,
    AddToGroupCommand,
    EditBlockParamsCommand,
    EditConnectionRouteCommand,
    GroupBlocksCommand,
    MoveProxyLayoutCommand,
    MoveResizeBlockCommand,
    MoveResizeGroupCommand,
    RemoveBlockCommand,
    RemoveConnectionCommand,
    RemoveFromGroupCommand,
    RemoveBoundaryPortCommand,
    RenameBoundaryPortCommand,
    RenameGroupCommand,
    PasteClipboardCommand,
    ToggleOrientationCommand,
    ToggleGroupOrientationCommand,
    ToggleProxyOrientationCommand,
    UngroupCommand,
    DeleteGroupCommand,
    WireManualBoundaryCommand,
    ConnectionSnapshot,
)

if TYPE_CHECKING:
    from pySimBlocks.gui.services.project_loader import ProjectLoader


class ProjectController(QObject):
    """Controller coordinating all mutations to the project model and diagram view.

    Acts as the single point of truth for block and connection lifecycle
    operations, dirty-state tracking, plot management, and simulation parameter
    updates.

    Attributes:
        project_state: Shared mutable state of the open project.
        view: The diagram canvas widget.
        resolve_block_meta: Callable returning :class:`BlockMeta` for a given
            category and block type.
        is_dirty: True if there are unsaved changes.
    """

    #: Signal emitted with the new dirty flag value whenever the unsaved-changes state changes.
    dirty_changed: Signal = Signal(bool)

    def __init__(
        self,
        project_state: ProjectState,
        view: DiagramView,
        resolve_block_meta: Callable[[str, str], BlockMeta],
        undo_manager: UndoManager,
    ):
        """Initialize the ProjectController.

        Args:
            project_state: Shared project state to read and mutate.
            view: The diagram view to keep in sync with the model.
            resolve_block_meta: Callable returning :class:`BlockMeta` for a
                given ``(category, block_type)`` pair.
        """
        super().__init__()
        self.project_state = project_state
        self.resolve_block_meta = resolve_block_meta
        self.view = view
        self.undo_manager = undo_manager

        self.is_dirty: bool = False


    # --------------------------------------------------------------------------
    # Block methods
    # --------------------------------------------------------------------------

    def add_block(
        self,
        category: str,
        block_type: str,
        block_layout: dict | None = None,
    ) -> BlockInstance:
        """Create and add a new block of the given type to the project.

        Args:
            category: Category name of the block.
            block_type: Type name of the block within the category.
            block_layout: Optional dict with position/size hints for the view.

        Returns:
            The newly created :class:`BlockInstance`.
        """
        block_meta = self.resolve_block_meta(category, block_type)
        block_instance = BlockInstance(block_meta)
        self.undo_manager.push(AddBlockCommand(self, block_instance, block_layout))
        return block_instance

    def add_copy_block(self, block_instance: BlockInstance) -> BlockInstance:
        """Add a copy of an existing block to the project.

        Args:
            block_instance: The block to copy.

        Returns:
            The newly created copy as a :class:`BlockInstance`.
        """
        copy_block = BlockInstance.copy(block_instance)
        self.undo_manager.push(AddBlockCommand(self, copy_block))
        return copy_block

    def copy_selection(self) -> bool:
        """Copy the current diagram selection to the view clipboard."""
        clipboard = capture_selection_clipboard(self)
        if clipboard is None:
            return False
        self.view.clipboard = clipboard
        self.view.paste_generation = 0
        return True

    def paste_clipboard_at(self, origin: QPointF) -> bool:
        """Paste the view clipboard at ``origin`` (undoable)."""
        clipboard = self.view.clipboard
        if not clipboard_has_content(clipboard):
            return False
        if clipboard.boundary_ports and self.view.current_view_group_uid is None:
            return False
        parent_uid = self.view.current_view_group_uid
        self.undo_manager.push(
            PasteClipboardCommand(self, clipboard, QPointF(origin), parent_uid)
        )
        self.view.paste_generation += 1
        return True

    def rename_block(self, block_instance: BlockInstance, new_name: str) -> None:
        """Rename a block and update all references in logging and plot signals.

        Args:
            block_instance: The block to rename.
            new_name: Desired new name. A unique suffix is appended if the name
                is already taken.
        """
        old_name = block_instance.name

        if old_name == new_name:
            return

        self.make_dirty()
        new_name = self.make_unique_name(new_name)

        block_instance.name = new_name
        prefix_old = f"{old_name}.outputs."
        prefix_new = f"{new_name}.outputs."

        self.project_state.logging = [
            s.replace(prefix_old, prefix_new)
            if s.startswith(prefix_old) else s
            for s in self.project_state.logging
        ]

        for plot in self.project_state.plots:
            plot["signals"] = [
                s.replace(prefix_old, prefix_new)
                if s.startswith(prefix_old) else s
                for s in plot["signals"]
            ]

    def update_block_param(self, block_instance: BlockInstance, params: dict[str, Any]) -> None:
        """Apply new parameter values to a block, refreshing ports and connections as needed.

        Args:
            block_instance: The block to update.
            params: New parameter dict. If a ``'name'`` key is present the
                block is also renamed.
        """
        self.undo_manager.push(EditBlockParamsCommand(self, block_instance, params))

    def remove_block(self, block_instance: BlockInstance) -> None:
        """Remove a block, its connections, and its signals from the project.

        Args:
            block_instance: The block to remove.
        """
        self.undo_manager.push(RemoveBlockCommand(self, block_instance))

    def group_blocks(
        self,
        blocks: list[BlockInstance],
        name: str | None = None,
        *,
        child_group_uids: list[str] | None = None,
        parent_uid: str | None = None,
    ) -> VisualGroup | None:
        """Create a visual group from blocks and/or child groups (undoable)."""
        unique_blocks: list[BlockInstance] = []
        seen = set()
        for block in blocks:
            if block.uid in seen:
                continue
            seen.add(block.uid)
            unique_blocks.append(block)

        child_uids = list(dict.fromkeys(child_group_uids or []))
        if parent_uid is None:
            parent_uid = self.view.current_view_group_uid

        if len(unique_blocks) + len(child_uids) < 2:
            return None

        for block in unique_blocks:
            if not self._block_at_view_level(block.uid, parent_uid):
                return None

        for child_uid in child_uids:
            child = self.project_state.get_visual_group(child_uid)
            if child is None or child.parent_uid != parent_uid:
                return None

        self.undo_manager.push(
            GroupBlocksCommand(
                self,
                unique_blocks,
                name,
                child_group_uids=child_uids,
                parent_uid=parent_uid,
            )
        )
        for group in reversed(self.project_state.visual_groups):
            if set(group.members) == {b.uid for b in unique_blocks} and set(
                group.child_group_uids
            ) == set(child_uids):
                return group
        return None

    def ungroup(self, group_uid: str) -> bool:
        """Remove a visual group by UID (undoable)."""
        if self.project_state.get_visual_group(group_uid) is None:
            return False
        self.undo_manager.push(UngroupCommand(self, group_uid))
        return True

    def delete_group(self, group_uid: str) -> bool:
        """Delete a visual group and all nested content (undoable)."""
        if self.project_state.get_visual_group(group_uid) is None:
            return False
        self.undo_manager.push(DeleteGroupCommand(self, group_uid))
        return True

    def group_selected_blocks(self) -> VisualGroup | None:
        """Group the current diagram selection of blocks and/or groups."""
        blocks = self.view.get_selected_block_instances()
        child_uids = self.view.get_selected_group_uids()
        if len(blocks) + len(child_uids) < 2:
            return None
        return self.group_blocks(
            blocks,
            child_group_uids=child_uids,
            parent_uid=self.view.current_view_group_uid,
        )

    def ungroup_selected_group(self) -> bool:
        """Ungroup the currently selected visual group."""
        group_uid = self.view.get_selected_group_uid()
        if group_uid is None:
            return False
        return self.ungroup(group_uid)

    def add_block_to_group(
        self,
        group_uid: str,
        block_instance: BlockInstance,
        layout: dict[str, Any] | None = None,
    ) -> bool:
        """Add an existing block to a visual group (undoable)."""
        if not self._can_add_block_to_group(group_uid, block_instance.uid):
            return False
        if layout is None:
            layout = self._capture_block_layout(block_instance)
        self.undo_manager.push(
            AddToGroupCommand(self, group_uid, block_instance.uid, layout)
        )
        return True

    def add_block_in_group_view(
        self,
        category: str,
        block_type: str,
        group_uid: str,
    ) -> BlockInstance | None:
        """Drop a new palette block into a group's internal view (undoable)."""
        if self.project_state.get_visual_group(group_uid) is None:
            return None
        self.begin_macro("Add to Group")
        try:
            block = self.add_block(category, block_type)
            layout = self._capture_block_layout(block)
            if not self.add_block_to_group(group_uid, block, layout):
                return None
            return block
        finally:
            self.end_macro()

    def remove_block_from_group(self, group_uid: str, block_uid: str) -> bool:
        """Remove a block from a visual group without deleting it (undoable)."""
        group = self.project_state.get_visual_group(group_uid)
        if group is None or block_uid not in group.members:
            return False
        self.undo_manager.push(RemoveFromGroupCommand(self, group_uid, block_uid))
        return True

    def try_wire_boundary_endpoints(self, src, dst) -> bool:
        """Wire group boundaries, proxies, or group-to-group borders."""
        from pySimBlocks.gui.graphics.group_item import GroupBoundaryPortItem
        from pySimBlocks.gui.graphics.group_proxy_item import GroupProxyPortItem
        from pySimBlocks.gui.graphics.port_item import PortItem

        boundary_ports = [
            endpoint
            for endpoint in (src, dst)
            if isinstance(endpoint, GroupBoundaryPortItem)
        ]
        if len(boundary_ports) == 2:
            return self._wire_group_boundaries_together(
                boundary_ports[0],
                boundary_ports[1],
            )

        proxy_port = None
        boundary_port = None
        block_port_item = None
        for endpoint in (src, dst):
            if isinstance(endpoint, GroupProxyPortItem):
                proxy_port = endpoint
            elif isinstance(endpoint, GroupBoundaryPortItem):
                boundary_port = endpoint
            elif isinstance(endpoint, PortItem):
                block_port_item = endpoint

        if proxy_port is not None and boundary_port is not None:
            return self._wire_proxy_to_child_group_border(proxy_port, boundary_port)

        if block_port_item is None:
            return False

        member_port = block_port_item.instance

        if proxy_port is not None:
            group_uid = self.view.current_view_group_uid
            if group_uid is None:
                return False
            boundary_uid = proxy_port.parent_proxy.boundary.uid
            return self._wire_manual_boundary_internal(
                group_uid,
                boundary_uid,
                member_port,
            )

        if boundary_port is not None:
            if self._wire_child_border_to_parent_member(boundary_port, member_port):
                return True
            group_uid = boundary_port.parent_group.group.uid
            boundary_uid = boundary_port.boundary.uid
            return self._wire_manual_boundary_external(
                group_uid,
                boundary_uid,
                member_port,
            )
        return False

    def _wire_child_border_to_parent_member(
        self,
        boundary_port,
        member_port: PortInstance,
    ) -> bool:
        """Wire a child-group border port to a direct member of the active parent."""
        active_uid = self.view.current_view_group_uid
        if active_uid is None:
            return False
        child_group = boundary_port.parent_group.group
        parent = self.project_state.get_visual_group(active_uid)
        if parent is None or child_group.parent_uid != parent.uid:
            return False
        if member_port.block.uid not in parent.members:
            return False
        boundary = boundary_port.boundary
        internal = find_port(self.project_state, boundary.linked_port_uid)
        if internal is None:
            return False
        if boundary.direction == "input":
            src_port, dst_port = member_port, internal
        else:
            src_port, dst_port = internal, member_port
        if not src_port.is_compatible(dst_port):
            return False
        dst_connections = self.project_state.get_connections_of_port(dst_port)
        if not dst_port.can_accept_connection(dst_connections):
            return False
        self.undo_manager.push(AddConnectionCommand(self, src_port, dst_port, None))
        return True

    def _wire_group_boundaries_together(
        self,
        port_a,
        port_b,
    ) -> bool:
        """Connect two group border ports across different groups."""
        group_a = port_a.parent_group.group
        group_b = port_b.parent_group.group
        if group_a.uid == group_b.uid:
            return False

        boundary_a = port_a.boundary
        boundary_b = port_b.boundary
        member_a = find_port(self.project_state, boundary_a.linked_port_uid)
        member_b = find_port(self.project_state, boundary_b.linked_port_uid)
        if member_a is None or member_b is None:
            return False

        if boundary_a.direction == "output" and boundary_b.direction == "input":
            src_port, dst_port = member_a, member_b
        elif boundary_a.direction == "input" and boundary_b.direction == "output":
            src_port, dst_port = member_b, member_a
        else:
            return False

        if not src_port.is_compatible(dst_port):
            return False
        dst_connections = self.project_state.get_connections_of_port(dst_port)
        if not dst_port.can_accept_connection(dst_connections):
            return False

        from pySimBlocks.gui.undo_redo.commands import AddConnectionCommand

        self.undo_manager.push(AddConnectionCommand(self, src_port, dst_port, None))
        return True

    def _wire_manual_boundary_internal(
        self,
        group_uid: str,
        boundary_uid: str,
        member_port: PortInstance,
    ) -> bool:
        group = self.project_state.get_visual_group(group_uid)
        if group is None:
            return False
        boundary = self._find_boundary_port(group, boundary_uid)
        if boundary is None or not self._validate_internal_link(
            group, boundary, member_port
        ):
            return False
        before = self._capture_boundary_wire_snapshot(group_uid, boundary_uid)
        after_wiring = capture_wiring_state(boundary)
        after_wiring.linked_port_uid = port_key(member_port)
        connection_snapshot = self._connection_snapshot_for_wiring(
            group, boundary, after_wiring
        )
        after = (after_wiring, connection_snapshot)
        self.undo_manager.push(
            WireManualBoundaryCommand(self, group_uid, boundary_uid, before, after)
        )
        return True

    def _validate_internal_link(
        self,
        group: VisualGroup,
        boundary: BoundaryPort,
        member_port: PortInstance,
    ) -> bool:
        """Validate an internal boundary link against the full group content."""
        content_uids = set(self._group_content_uids_for_group(group))
        return validate_internal_link(
            group,
            boundary,
            member_port,
            content_uids=content_uids,
        )

    def _wire_proxy_to_child_group_border(
        self,
        proxy_port,
        child_boundary_port,
    ) -> bool:
        """Wire a parent-group proxy to a child group's border port."""
        active_uid = self.view.current_view_group_uid
        if active_uid is None:
            return False

        parent_group = self.project_state.get_visual_group(active_uid)
        child_group = child_boundary_port.parent_group.group
        if parent_group is None or child_group.uid not in parent_group.child_group_uids:
            return False

        boundary_uid = proxy_port.parent_proxy.boundary.uid
        boundary = self._find_boundary_port(parent_group, boundary_uid)
        if boundary is None:
            return False

        member_port = find_port(
            self.project_state,
            child_boundary_port.boundary.linked_port_uid,
        )
        if member_port is None:
            return False

        return self._wire_manual_boundary_internal(
            active_uid,
            boundary_uid,
            member_port,
        )

    def _wire_auto_boundary_internal(
        self,
        group_uid: str,
        boundary_uid: str,
        member_port: PortInstance,
    ) -> bool:
        """Restore an auto boundary by wiring its proxy to the member port."""
        group = self.project_state.get_visual_group(group_uid)
        if group is None:
            return False
        boundary = self._find_boundary_port(group, boundary_uid)
        if boundary is None or boundary.origin != "auto" or boundary.linked_connection_uid:
            return False
        if not self._validate_internal_link(group, boundary, member_port):
            return False
        if not boundary.external_port_uid:
            return False
        external = find_port(self.project_state, boundary.external_port_uid)
        if external is None:
            return False
        if boundary.direction == "input":
            src_port, dst_port = external, member_port
        else:
            src_port, dst_port = member_port, external
        if not src_port.is_compatible(dst_port):
            return False
        dst_connections = self.project_state.get_connections_of_port(dst_port)
        if not dst_port.can_accept_connection(dst_connections):
            return False
        self.undo_manager.push(AddConnectionCommand(self, src_port, dst_port, None))
        return True

    def _validate_auto_external_link(
        self,
        group: VisualGroup,
        boundary: BoundaryPort,
        external_port: PortInstance,
    ) -> PortInstance | None:
        """Return the internal port when an incomplete auto boundary may be rewired."""
        if boundary.origin != "auto" or boundary.linked_connection_uid:
            return None
        if not boundary.linked_port_uid:
            return None
        internal = find_port(self.project_state, boundary.linked_port_uid)
        if internal is None:
            return None
        members = set(self._group_content_uids_for_group(group))
        if external_port.block.uid in members:
            return None
        if boundary.direction == "input":
            if external_port.direction != "output" or internal.direction != "input":
                return None
            src_port, dst_port = external_port, internal
        else:
            if external_port.direction != "input" or internal.direction != "output":
                return None
            src_port, dst_port = internal, external_port
        if not src_port.is_compatible(dst_port):
            return None
        dst_connections = self.project_state.get_connections_of_port(dst_port)
        if not dst_port.can_accept_connection(dst_connections):
            return None
        return internal

    def _wire_auto_boundary_external(
        self,
        group_uid: str,
        boundary_uid: str,
        external_port: PortInstance,
    ) -> bool:
        group = self.project_state.get_visual_group(group_uid)
        if group is None:
            return False
        boundary = self._find_boundary_port(group, boundary_uid)
        if boundary is None:
            return False
        internal = self._validate_auto_external_link(group, boundary, external_port)
        if internal is None:
            return False
        if boundary.direction == "input":
            src_port, dst_port = external_port, internal
        else:
            src_port, dst_port = internal, external_port
        self.undo_manager.push(AddConnectionCommand(self, src_port, dst_port, None))
        return True

    def _wire_manual_boundary_external(
        self,
        group_uid: str,
        boundary_uid: str,
        external_port: PortInstance,
    ) -> bool:
        group = self.project_state.get_visual_group(group_uid)
        if group is None:
            return False
        boundary = self._find_boundary_port(group, boundary_uid)
        if boundary is None or not validate_external_link(group, boundary, external_port):
            return False
        before = self._capture_boundary_wire_snapshot(group_uid, boundary_uid)
        after_wiring = capture_wiring_state(boundary)
        after_wiring.external_port_uid = port_key(external_port)
        connection_snapshot = self._connection_snapshot_for_wiring(
            group, boundary, after_wiring
        )
        after = (after_wiring, connection_snapshot)
        self.undo_manager.push(
            WireManualBoundaryCommand(self, group_uid, boundary_uid, before, after)
        )
        return True

    def _find_boundary_port(
        self,
        group: VisualGroup,
        boundary_uid: str,
    ) -> BoundaryPort | None:
        return next(
            (port for port in group.boundary_ports if port.uid == boundary_uid),
            None,
        )

    def _capture_boundary_wire_snapshot(
        self,
        group_uid: str,
        boundary_uid: str,
    ) -> tuple[BoundaryWiringState, ConnectionSnapshot | None]:
        group = self.project_state.get_visual_group(group_uid)
        if group is None:
            return BoundaryWiringState(), None
        boundary = self._find_boundary_port(group, boundary_uid)
        if boundary is None:
            return BoundaryWiringState(), None
        connection = find_connection_for_boundary(self.project_state, boundary)
        snapshot = (
            self._capture_connection_snapshot(connection)
            if connection is not None
            else None
        )
        return capture_wiring_state(boundary), snapshot

    def _connection_snapshot_for_wiring(
        self,
        group: VisualGroup,
        boundary: BoundaryPort,
        wiring: BoundaryWiringState,
    ) -> ConnectionSnapshot | None:
        trial = BoundaryPort(
            uid=boundary.uid,
            direction=boundary.direction,
            linked_port_uid=wiring.linked_port_uid,
            external_port_uid=wiring.external_port_uid,
            origin="manual",
        )
        if not can_complete(self.project_state, trial):
            return None
        endpoints = connection_endpoints(self.project_state, trial)
        if endpoints is None:
            return None
        src_port, dst_port = endpoints
        return ConnectionSnapshot(
            src_block_uid=src_port.block.uid,
            src_port_name=src_port.name,
            dst_block_uid=dst_port.block.uid,
            dst_port_name=dst_port.name,
            points=None,
        )

    def _apply_boundary_wire_snapshot(
        self,
        group_uid: str,
        boundary_uid: str,
        wiring: BoundaryWiringState,
        connection_snapshot: ConnectionSnapshot | None,
    ) -> None:
        group = self.project_state.get_visual_group(group_uid)
        if group is None:
            return
        boundary = self._find_boundary_port(group, boundary_uid)
        if boundary is None:
            return

        existing = find_connection_for_boundary(self.project_state, boundary)
        if existing is not None:
            self._remove_connection(existing, refresh_boundaries=False)

        apply_wiring_state(boundary, wiring)
        if boundary.origin == "manual" and wiring.linked_port_uid:
            self._remove_auto_boundaries_for_member_port(
                group, wiring.linked_port_uid, keep_uid=boundary_uid
            )
        if connection_snapshot is not None:
            connection = self._add_connection_from_snapshot(connection_snapshot)
            if connection is not None:
                boundary.linked_connection_uid = self._connection_key(connection)
        else:
            boundary.linked_connection_uid = ""

        self.view.refresh_visual_groups()

    def boundary_port_flow_label(
        self,
        group: VisualGroup,
        boundary: BoundaryPort,
    ) -> str:
        """Return the flow label for a boundary (source for In, destination for Out)."""
        return boundary_port_label(self.project_state, group, boundary)

    def boundary_proxy_label(self, boundary: BoundaryPort) -> str:
        """Return the label drawn on a GroupIn/GroupOut proxy."""
        if boundary.origin == "manual":
            return manual_boundary_display_label(boundary)
        if boundary.label.strip():
            return boundary.label.strip()
        linked = find_port(self.project_state, boundary.linked_port_uid)
        if linked is None:
            return ""
        return str(linked.display_as or linked.name)

    def rename_boundary_port(
        self,
        group_uid: str,
        boundary_uid: str,
        new_label: str,
    ) -> bool:
        """Rename one proxy label (empty string resets automatic label)."""
        group = self.project_state.get_visual_group(group_uid)
        if group is None:
            return False
        boundary = self._find_boundary_port(group, boundary_uid)
        if boundary is None:
            return False
        trimmed = new_label.strip()
        if trimmed == boundary.label:
            return False
        self.undo_manager.push(
            RenameBoundaryPortCommand(
                self,
                group_uid,
                boundary_uid,
                boundary.label,
                trimmed,
            )
        )
        return True

    def rename_visual_group(self, group_uid: str, new_name: str) -> bool:
        """Rename a visual group (undoable)."""
        group = self.project_state.get_visual_group(group_uid)
        if group is None:
            return False
        trimmed = new_name.strip()
        if not trimmed or trimmed == group.name:
            return False
        unique_name = self._make_unique_group_name(trimmed, exclude_uid=group_uid)
        self.undo_manager.push(
            RenameGroupCommand(self, group_uid, group.name, unique_name)
        )
        return True

    def make_unique_name(self, base_name: str) -> str:
        """Return ``base_name`` or a suffixed variant that is unique across all blocks.

        Args:
            base_name: Desired block name.

        Returns:
            ``base_name`` if available, otherwise ``base_name_N`` for the
            smallest N that is not already taken.
        """
        existing = {b.name for b in self.project_state.blocks}

        if base_name not in existing:
            return base_name

        i = 1
        while f"{base_name}_{i}" in existing:
            i += 1

        return f"{base_name}_{i}"

    def is_name_available(self, name: str, current=None) -> bool:
        """Return True if ``name`` is not already used by another block.

        Args:
            name: Name to check for availability.
            current: Block instance to exclude from the check (e.g. the block
                being renamed).

        Returns:
            True if the name is free, False if it is taken by another block.
        """
        for b in self.project_state.blocks:
            if b is current:
                continue
            if b.name == name:
                return False
        return True


    # --------------------------------------------------------------------------
    # Connection methods
    # --------------------------------------------------------------------------

    def try_connect_boundary_ports(
        self,
        port1: PortInstance,
        port2: PortInstance,
    ) -> bool:
        """Complete or wire a manual group boundary instead of a direct connection."""
        if port1 is port2:
            return False

        src_group = self._group_containing_member(port1.block.uid)
        dst_group = self._group_containing_member(port2.block.uid)
        if (
            src_group is not None
            and dst_group is not None
            and src_group.uid != dst_group.uid
        ):
            return False

        ports = {port1, port2}
        for group in self.project_state.visual_groups:
            for boundary in group.boundary_ports:
                if boundary.linked_connection_uid:
                    continue

                internal = (
                    find_port(self.project_state, boundary.linked_port_uid)
                    if boundary.linked_port_uid
                    else None
                )
                external = (
                    find_port(self.project_state, boundary.external_port_uid)
                    if boundary.external_port_uid
                    else None
                )

                if (
                    internal is not None
                    and external is not None
                    and ports == {internal, external}
                ):
                    return self._complete_manual_boundary(group.uid, boundary.uid)

                if internal is not None and internal in ports:
                    external_candidate = port2 if port1 is internal else port1
                    if validate_external_link(group, boundary, external_candidate):
                        return self._wire_manual_boundary_external(
                            group.uid,
                            boundary.uid,
                            external_candidate,
                        )

                if external is not None and external in ports:
                    internal_candidate = port2 if port1 is external else port1
                    if self._validate_internal_link(
                        group, boundary, internal_candidate
                    ):
                        return self._wire_manual_boundary_internal(
                            group.uid,
                            boundary.uid,
                            internal_candidate,
                        )
        return False

    def _complete_manual_boundary(self, group_uid: str, boundary_uid: str) -> bool:
        group = self.project_state.get_visual_group(group_uid)
        if group is None:
            return False
        boundary = self._find_boundary_port(group, boundary_uid)
        if boundary is None or not can_complete(self.project_state, boundary):
            return False
        before = self._capture_boundary_wire_snapshot(group_uid, boundary_uid)
        wiring = capture_wiring_state(boundary)
        connection_snapshot = self._connection_snapshot_for_wiring(
            group, boundary, wiring
        )
        if connection_snapshot is None:
            return False
        self.undo_manager.push(
            WireManualBoundaryCommand(
                self,
                group_uid,
                boundary_uid,
                before,
                (wiring, connection_snapshot),
            )
        )
        return True

    def add_connection(
        self,
        port1: PortInstance,
        port2: PortInstance,
        points: list[QPointF] | None = None,
    ) -> None:
        """Create a connection between two ports if compatible.

        The method silently returns without creating a connection if the ports
        are not compatible or if the destination port cannot accept another
        connection.

        Args:
            port1: First port (output or input).
            port2: Second port (input or output).
            points: Optional list of intermediate waypoints for the wire.
        """
        if self.try_connect_boundary_ports(port1, port2):
            return
        if not port1.is_compatible(port2):
            return
        src_port, dst_port = (
            (port1, port2) if port1.direction == "output" else (port2, port1)
        )
        port_dst_connections = self.project_state.get_connections_of_port(dst_port)
        if not dst_port.can_accept_connection(port_dst_connections):
            return
        self.undo_manager.push(AddConnectionCommand(self, src_port, dst_port, points))

    def remove_connection(self, connection: ConnectionInstance) -> None:
        """Remove a connection from both the model and the view.

        Args:
            connection: The :class:`ConnectionInstance` to remove.
        """
        self.undo_manager.push(RemoveConnectionCommand(self, connection))

    def execute_move_resize_block(
        self,
        block_instance: BlockInstance,
        old_pos: QPointF,
        old_rect: QRectF,
        new_pos: QPointF,
        new_rect: QRectF,
    ) -> None:
        self.undo_manager.push(
            MoveResizeBlockCommand(
                self, block_instance.uid, old_pos, old_rect, new_pos, new_rect
            )
        )

    def execute_move_resize_group(
        self,
        group_uid: str,
        old_pos: QPointF,
        old_rect: QRectF,
        new_pos: QPointF,
        new_rect: QRectF,
    ) -> None:
        if old_pos == new_pos and old_rect == new_rect:
            return
        self.undo_manager.push(
            MoveResizeGroupCommand(
                self, group_uid, old_pos, old_rect, new_pos, new_rect
            )
        )

    def execute_toggle_orientation(self, block_instance: BlockInstance) -> None:
        block_item = self.view.get_block_item_from_instance(block_instance)
        if block_item is None:
            return
        old_orientation = block_item.orientation
        new_orientation = "flipped" if old_orientation == "normal" else "normal"
        self.undo_manager.push(
            ToggleOrientationCommand(self, block_instance.uid, old_orientation, new_orientation)
        )

    def execute_toggle_group_orientation(self, group_uid: str) -> None:
        group_item = self.view.group_items.get(group_uid)
        if group_item is None:
            return
        old_orientation = group_item.orientation
        new_orientation = "flipped" if old_orientation == "normal" else "normal"
        self.undo_manager.push(
            ToggleGroupOrientationCommand(self, group_uid, old_orientation, new_orientation)
        )

    def execute_toggle_proxy_orientation(self, group_uid: str, boundary_uid: str) -> None:
        proxy_item = self.view.proxy_items.get(boundary_uid)
        if proxy_item is None:
            return
        old_orientation = proxy_item.orientation
        new_orientation = "flipped" if old_orientation == "normal" else "normal"
        self.undo_manager.push(
            ToggleProxyOrientationCommand(
                self, group_uid, boundary_uid, old_orientation, new_orientation
            )
        )

    def execute_edit_connection_route(
        self,
        connection: ConnectionInstance,
        old_points: list[QPointF] | None,
        new_points: list[QPointF] | None,
    ) -> None:
        from pySimBlocks.gui.undo_redo.commands import routes_equal

        if routes_equal(old_points, new_points):
            return
        self.undo_manager.push(
            EditConnectionRouteCommand(self, connection, old_points, new_points)
        )

    def execute_move_proxy_layout(
        self,
        group_uid: str,
        boundary_uid: str,
        old_pos: QPointF,
        new_pos: QPointF,
    ) -> None:
        if old_pos == new_pos:
            return
        self.undo_manager.push(
            MoveProxyLayoutCommand(self, group_uid, boundary_uid, old_pos, new_pos)
        )

    def begin_macro(self, text: str) -> None:
        self.undo_manager.stack.beginMacro(text)

    def end_macro(self) -> None:
        self.undo_manager.stack.endMacro()


    # --------------------------------------------------------------------------
    # Project methods
    # --------------------------------------------------------------------------

    def make_dirty(self) -> None:
        """Mark the project as having unsaved changes and emit :attr:`dirty_changed`."""
        if not self.is_dirty:
            self.is_dirty = True
            self.dirty_changed.emit(True)

    def mark_gui_layout_dirty(self) -> None:
        """Mark GUI-only layout edits that stay outside the undo/redo stack."""
        self.make_dirty()

    def clear_dirty(self) -> None:
        """Clear the unsaved-changes flag and emit :attr:`dirty_changed`."""
        if self.is_dirty:
            self.is_dirty = False
            self.dirty_changed.emit(False)

    def clear(self) -> None:
        """Reset the project state and diagram view to an empty state."""
        self.project_state.clear()
        self.view.clear_scene()
        self.view.view_stack = []
        self.view.view_stack_changed.emit()
        self.undo_manager.clear()
        self.clear_dirty()

    def update_project_param(self, new_path: Path, ext: str) -> None:
        """Update the project directory path and external module reference.

        Args:
            new_path: New project directory path.
            ext: New external module path string, or ``''`` to clear it.
        """
        cleanup_runtime_project_yaml(self.project_state.directory_path)
        if new_path != self.project_state.directory_path:
            self.make_dirty()
        self.project_state.directory_path = new_path

        if ext != self.project_state.external:
            self.make_dirty()
        self.project_state.external = None if ext == "" else ext

    def load_project(self, loader: "ProjectLoader") -> None:
        """Delegate project loading to the given loader service.

        Args:
            loader: A :class:`ProjectLoader` implementation that reads the
                project files and populates this controller.
        """
        loader.load(self, self.project_state.directory_path)
        for group in self.project_state.visual_groups:
            self.ensure_group_boundary_proxies(group)
        for group in self.project_state.visual_groups:
            self.apply_member_layouts(group)
        self.view.refresh_visual_groups()


    # --------------------------------------------------------------------------
    # Plot methods
    # --------------------------------------------------------------------------

    def create_plot(self, title: str, signals: list[str], mode: str = "auto") -> None:
        """Append a new plot to the project configuration.

        Args:
            title: Title of the plot figure.
            signals: List of signal names to display in the plot. Any signal
                not already logged is automatically added to the logging list.
            mode: Plot display mode (``auto``, ``overlay``, ``split_signals``,
                or ``split_components``).
        """
        self._ensure_logged(signals)
        self.project_state.plots.append({
            "title": title,
            "signals": list(signals),
            "mode": mode,
        })
        self.make_dirty()

    def update_plot(
        self,
        index: int,
        title: str,
        signals: list[str],
        mode: str = "auto",
        series_styles: dict[str, dict[str, str]] | None = None,
    ) -> None:
        """Update the title and signals of an existing plot.

        Args:
            index: Index of the plot in :attr:`ProjectState.plots`.
            title: New title for the plot.
            signals: New list of signal names. Any signal not yet logged is
                automatically added.
            mode: Plot display mode (``auto``, ``overlay``, ``split_signals``,
                or ``split_components``).
            series_styles: Optional per-component style map for YAML storage.
        """
        self._ensure_logged(signals)
        plot = self.project_state.plots[index]
        styles_unchanged = series_styles is None or plot.get("series_styles") == series_styles
        if (
            plot["signals"] == signals
            and plot["title"] == title
            and str(plot.get("mode", "auto")) == mode
            and styles_unchanged
        ):
            return
        plot["title"] = title
        plot["signals"] = list(signals)
        plot["mode"] = mode
        if series_styles is not None:
            if series_styles:
                plot["series_styles"] = series_styles
            else:
                plot.pop("series_styles", None)
        self.make_dirty()

    def delete_plot(self, index: int) -> None:
        """Remove a plot by index.

        Args:
            index: Index of the plot in :attr:`ProjectState.plots`.
        """
        del self.project_state.plots[index]
        self.make_dirty()

    def _ensure_logged_manual_layout(self, plot: dict) -> None:
        """Ensure all signals referenced in a manual layout preset are logged."""
        for panel in plot.get("panels", []):
            if not isinstance(panel, dict):
                continue
            selection = panel.get("selection", {})
            if isinstance(selection, dict):
                self._ensure_logged(list(selection.keys()))

    def add_manual_layout_preset(self, plot: dict) -> int:
        """Append a manual multi-panel layout preset to the project.

        Args:
            plot: Plot descriptor with ``layout: manual`` and ``panels``.

        Returns:
            Index of the new preset in :attr:`ProjectState.plots`.
        """
        self._ensure_logged_manual_layout(plot)
        self.project_state.plots.append(plot)
        self.make_dirty()
        return len(self.project_state.plots) - 1

    def update_manual_layout_preset(self, index: int, plot: dict) -> None:
        """Replace an existing manual layout preset at ``index``.

        Args:
            index: Index in :attr:`ProjectState.plots`.
            plot: Plot descriptor with ``layout: manual`` and ``panels``.
        """
        self._ensure_logged_manual_layout(plot)
        self.project_state.plots[index] = plot
        self.make_dirty()

    def update_simulation_params(self, params: dict[str, float | str]) -> None:
        """Apply new simulation parameters to the project state.

        Args:
            params: Dict of simulation parameters (e.g. ``dt``, ``T``).
        """
        if self.project_state.simulation.__dict__ == params:
            return
        self.project_state.load_simulation(params)
        self.make_dirty()

    def set_logged_signals(self, signals: list[str]) -> None:
        """Replace the logging list with ``signals``, preserving insertion order.

        Args:
            signals: New list of signal names to log. Duplicates are removed
                while preserving the first occurrence.
        """
        new_logging = list(dict.fromkeys(signals))
        if set(self.project_state.logging) == set(new_logging):
            return
        self.project_state.logging = new_logging
        self.make_dirty()


    # --------------------------------------------------------------------------
    # Private methods
    # --------------------------------------------------------------------------

    def _add_block(
        self,
        block_instance: BlockInstance,
        block_layout: dict | None = None,
    ) -> BlockInstance:
        """Register a block instance in the model and add its visual item to the view."""
        self.make_dirty()
        block_instance.name = self.make_unique_name(block_instance.name)
        block_instance.resolve_ports()
        self.project_state.add_block(block_instance)
        layout = dict(block_layout or {})
        self.view.add_block(block_instance, layout)
        block_item = self.view.get_block_item_from_instance(block_instance)
        if block_item is not None and ("x" in layout or "y" in layout):
            self._apply_block_layout(block_item, layout)
        self.view.refresh_visual_groups()

        return block_instance

    def _remove_connection_if_port_disapear(self, block_instance: BlockInstance) -> list[ConnectionSnapshot]:
        """Remove any connection whose source or destination port no longer exists."""
        removed: list[ConnectionSnapshot] = []
        for connection in self.project_state.get_connections_of_block(block_instance):
            src_exists = connection.src_port in connection.src_block().ports
            dst_exists = connection.dst_port in connection.dst_block().ports
            if not (src_exists and dst_exists):
                removed.append(self._capture_connection_snapshot(connection))
                self._remove_connection(connection)
        return removed

    def _ensure_logged(self, signals: list[str]) -> None:
        """Append any signal not yet in the logging list."""
        for sig in signals:
            if sig not in self.project_state.logging:
                self.project_state.logging.append(sig)

    def _remove_block(self, block_instance: BlockInstance) -> None:
        block_uid = block_instance.uid
        for connection in list(self.project_state.get_connections_of_block(block_instance)):
            self._remove_connection(connection, refresh_boundaries=False)

        removed_signals = [
            f"{block_instance.name}.outputs.{p.name}"
            for p in block_instance.ports if p.direction == "output"
        ]
        self.project_state.logging = [s for s in self.project_state.logging if s not in removed_signals]

        for group in self.project_state.visual_groups:
            if block_uid in group.members:
                self._remove_boundaries_for_member(group, block_uid)

        for i in reversed(range(len(self.project_state.plots))):
            plot = self.project_state.plots[i]
            if str(plot.get("layout", "")).strip().lower() == "manual":
                panels = plot.get("panels", [])
                if not isinstance(panels, list):
                    continue
                kept_panels = []
                for panel in panels:
                    if not isinstance(panel, dict):
                        continue
                    selection = panel.get("selection")
                    if isinstance(selection, dict):
                        new_sel = {
                            sig: [lbl for lbl in labels if lbl not in removed_signals]
                            for sig, labels in selection.items()
                            if sig not in removed_signals
                        }
                        new_sel = {sig: labels for sig, labels in new_sel.items() if labels}
                        if new_sel:
                            panel = dict(panel)
                            panel["selection"] = new_sel
                            kept_panels.append(panel)
                        continue
                    signals = panel.get("signals", [])
                    if isinstance(signals, list):
                        signals = [s for s in signals if s not in removed_signals]
                        if signals:
                            panel = dict(panel)
                            panel["signals"] = signals
                            kept_panels.append(panel)
                if kept_panels:
                    plot["panels"] = kept_panels
                else:
                    del self.project_state.plots[i]
                continue
            if "signals" not in plot:
                continue
            plot["signals"] = [s for s in plot["signals"] if s not in removed_signals]
            if not plot["signals"]:
                del self.project_state.plots[i]

        self.project_state.remove_block(block_instance)
        self.view.remove_block(block_instance)
        self._refresh_boundaries_for_member_uids({block_uid})

    def _remove_connection(
        self,
        connection: ConnectionInstance,
        *,
        refresh_boundaries: bool = True,
    ) -> None:
        block_uids = {connection.src_block().uid, connection.dst_block().uid}
        self._preserve_boundaries_on_connection_remove(connection)
        self.project_state.remove_connection(connection)
        self.view.remove_connection(connection)
        if refresh_boundaries:
            self._refresh_boundaries_for_member_uids(block_uids)

    def _capture_boundaries_for_connection(
        self,
        connection: ConnectionInstance,
    ) -> list[tuple[str, dict[str, Any]]]:
        """Snapshot group boundaries tied to a diagram connection (for undo)."""
        key = self._connection_key(connection)
        captured: list[tuple[str, dict[str, Any]]] = []
        seen: set[tuple[str, str]] = set()
        for group in self.project_state.visual_groups:
            for boundary in group.boundary_ports:
                linked = find_connection_for_boundary(self.project_state, boundary)
                if linked is not connection and boundary.linked_connection_uid != key:
                    continue
                item = (group.uid, boundary.uid)
                if item in seen:
                    continue
                seen.add(item)
                captured.append((group.uid, copy.deepcopy(boundary.to_dict())))
        return captured

    def _view_is_inside_group(self, view_group_uid: str | None, group: VisualGroup) -> bool:
        """Return whether the active view is inside a group or one of its descendants."""
        if view_group_uid is None:
            return False
        if view_group_uid == group.uid:
            return True
        child = self.project_state.get_visual_group(view_group_uid)
        while child is not None and child.parent_uid:
            if child.parent_uid == group.uid:
                return True
            child = self.project_state.get_visual_group(child.parent_uid)
        return False

    def _preserve_boundaries_on_connection_remove(
        self,
        connection: ConnectionInstance,
    ) -> None:
        """Keep boundary proxies wired but mark affected boundaries incomplete."""
        key = self._connection_key(connection)
        src_uid = connection.src_block().uid
        dst_uid = connection.dst_block().uid
        view_group_uid = self.view.current_view_group_uid
        changed = False

        for group in self.project_state.visual_groups:
            members = set(self._group_content_uids_for_group(group))
            src_in = src_uid in members
            dst_in = dst_uid in members
            if src_in == dst_in:
                continue

            internal_port = connection.dst_port if dst_in else connection.src_port
            external_port = connection.src_port if dst_in else connection.dst_port
            internal_key = port_key(internal_port)
            external_key = port_key(external_port)

            boundary = next(
                (
                    port
                    for port in group.boundary_ports
                    if port.linked_connection_uid == key
                    or (
                        port.linked_port_uid == internal_key
                        and find_connection_for_boundary(self.project_state, port)
                        is connection
                    )
                ),
                None,
            )
            if boundary is None:
                continue

            external_group = self._group_containing_member(external_port.block.uid)
            is_cross_group = (
                external_group is not None and external_group.uid != group.uid
            )
            external_at_root = external_group is None
            deleting_inside = self._view_is_inside_group(view_group_uid, group)

            if is_cross_group:
                boundary.linked_connection_uid = ""
                if boundary.origin == "manual" and boundary.external_port_uid == external_key:
                    boundary.external_port_uid = ""
                elif boundary.origin != "manual":
                    if deleting_inside:
                        boundary.external_port_uid = external_key
                        boundary.linked_port_uid = ""
                    else:
                        boundary.linked_port_uid = internal_key
                        boundary.external_port_uid = ""
                changed = True
                continue

            if external_at_root and boundary.origin != "manual":
                boundary.linked_connection_uid = ""
                if deleting_inside:
                    boundary.external_port_uid = external_key
                    boundary.linked_port_uid = ""
                else:
                    boundary.linked_port_uid = internal_key
                    boundary.external_port_uid = ""
                changed = True
                continue

            if boundary.origin == "manual":
                boundary.linked_connection_uid = ""
                if deleting_inside:
                    boundary.external_port_uid = external_key
                    boundary.linked_port_uid = ""
                elif external_at_root:
                    boundary.linked_port_uid = internal_key
                    boundary.external_port_uid = ""
                else:
                    if not boundary.linked_port_uid:
                        boundary.linked_port_uid = internal_key
                    if not boundary.external_port_uid:
                        boundary.external_port_uid = external_key
            else:
                boundary.linked_connection_uid = ""
                if deleting_inside:
                    boundary.external_port_uid = external_key
                    boundary.linked_port_uid = ""
                else:
                    boundary.linked_port_uid = internal_key
                    boundary.external_port_uid = ""

            self.ensure_group_boundary_proxies(group)
            changed = True

        if changed:
            self.view.refresh_visual_groups()

    def _restore_boundary_snapshots(
        self,
        snapshots: list[tuple[str, dict[str, Any]]],
    ) -> None:
        for group_uid, boundary_dict in snapshots:
            group = self.project_state.get_visual_group(group_uid)
            if group is None:
                continue
            restored = BoundaryPort.from_dict(boundary_dict)
            replaced = False
            for index, boundary in enumerate(group.boundary_ports):
                if boundary.uid == restored.uid:
                    group.boundary_ports[index] = restored
                    replaced = True
                    break
            if not replaced:
                group.boundary_ports.append(restored)
            self.ensure_group_boundary_proxies(group)
        self.view.refresh_visual_groups()

    def _find_block_by_uid(self, block_uid: str) -> BlockInstance | None:
        for block in self.project_state.blocks:
            if block.uid == block_uid:
                return block
        return None

    def _find_port(self, block_uid: str, port_name: str) -> PortInstance | None:
        block = self._find_block_by_uid(block_uid)
        if block is None:
            return None
        for port in block.ports:
            if port.name == port_name:
                return port
        return None

    def _capture_block_layout(self, block_instance: BlockInstance) -> dict:
        block_item = self.view.get_block_item_from_instance(block_instance)
        if block_item is None:
            return {}
        pos = block_item.pos()
        rect = block_item.rect()
        return {
            "x": float(pos.x()),
            "y": float(pos.y()),
            "orientation": block_item.orientation,
            "width": float(rect.width()),
            "height": float(rect.height()),
        }

    def _capture_connection_snapshot(self, connection: ConnectionInstance) -> ConnectionSnapshot:
        points: list[QPointF] | None = None
        connection_item = self.view.connections.get(connection)
        if (
            connection_item is not None
            and connection_item.is_manual
            and connection_item.route is not None
        ):
            points = [QPointF(p) for p in connection_item.route.points]
        return ConnectionSnapshot(
            src_block_uid=connection.src_block().uid,
            src_port_name=connection.src_port.name,
            dst_block_uid=connection.dst_block().uid,
            dst_port_name=connection.dst_port.name,
            points=points,
        )

    def _add_connection_from_snapshot(
        self,
        snapshot: ConnectionSnapshot,
        *,
        refresh_boundaries: bool = True,
    ) -> ConnectionInstance | None:
        src_port = self._find_port(snapshot.src_block_uid, snapshot.src_port_name)
        dst_port = self._find_port(snapshot.dst_block_uid, snapshot.dst_port_name)
        if src_port is None or dst_port is None:
            return None
        if not src_port.is_compatible(dst_port):
            return None
        if not dst_port.can_accept_connection(self.project_state.get_connections_of_port(dst_port)):
            return None
        connection_instance = ConnectionInstance(src_port, dst_port)
        self.project_state.add_connection(connection_instance)
        self.view.add_connection(connection_instance, snapshot.points)
        if refresh_boundaries:
            self._refresh_boundaries_for_member_uids(
                {src_port.block.uid, dst_port.block.uid}
            )
        return connection_instance

    def _set_group_geometry(self, group_uid: str, pos: QPointF, rect: QRectF) -> None:
        group = self.project_state.get_visual_group(group_uid)
        if group is None:
            return
        group_item = self.view.group_items.get(group_uid)
        if group_item is None:
            layout = dict(group.layout or {})
            layout.update({
                "x": float(pos.x()),
                "y": float(pos.y()),
                "width": float(rect.width()),
                "height": float(rect.height()),
            })
            group.layout = layout
            return
        group_item.apply_geometry(pos, rect)
        self.view.on_group_moved(group_item)

    def _set_group_orientation(self, group_uid: str, orientation: str) -> None:
        group_item = self.view.group_items.get(group_uid)
        if group_item is None:
            return
        group_item.set_orientation(orientation)

    def _set_proxy_orientation(
        self, group_uid: str, boundary_uid: str, orientation: str
    ) -> None:
        proxy_item = self.view.proxy_items.get(boundary_uid)
        if proxy_item is None:
            return
        proxy_item.set_orientation(orientation)

    def _set_block_geometry(self, block_uid: str, pos: QPointF, rect: QRectF) -> None:
        block = self._find_block_by_uid(block_uid)
        if block is None:
            return
        block_item = self.view.get_block_item_from_instance(block)
        if block_item is None:
            return
        block_item.setPos(QPointF(pos))
        block_item.setRect(0, 0, rect.width(), rect.height())
        block_item._layout_ports()
        self.view.on_block_moved(block_item)

    def _set_block_orientation(self, block_uid: str, orientation: str) -> None:
        block = self._find_block_by_uid(block_uid)
        if block is None:
            return
        block_item = self.view.get_block_item_from_instance(block)
        if block_item is None:
            return
        block_item.set_orientation(orientation)
        self.view.on_block_moved(block_item)

    def _apply_block_update(
        self,
        block_instance: BlockInstance,
        new_name: str,
        params: dict[str, Any],
    ) -> list[ConnectionSnapshot]:
        old_name = block_instance.name
        if old_name != new_name:
            new_name = self.make_unique_name(new_name)
            block_instance.name = new_name
            prefix_old = f"{old_name}.outputs."
            prefix_new = f"{new_name}.outputs."
            self.project_state.logging = [
                s.replace(prefix_old, prefix_new)
                if s.startswith(prefix_old) else s
                for s in self.project_state.logging
            ]
            for plot in self.project_state.plots:
                plot["signals"] = [
                    s.replace(prefix_old, prefix_new)
                    if s.startswith(prefix_old) else s
                    for s in plot["signals"]
                ]

        if params != block_instance.parameters:
            block_instance.update_params(params)
            block_instance.resolve_ports()
            removed = self._remove_connection_if_port_disapear(block_instance)
            self.view.refresh_block_port(block_instance)
            return removed
        return []

    def _create_visual_group(
        self,
        blocks: list[BlockInstance],
        name: str | None = None,
        *,
        child_group_uids: list[str] | None = None,
        parent_uid: str | None = None,
    ) -> VisualGroup:
        """Create and register a visual group without pushing undo."""
        if parent_uid is None:
            parent_uid = self.view.current_view_group_uid

        member_uids = [b.uid for b in blocks]
        child_uids = list(dict.fromkeys(child_group_uids or []))
        content_uids = self._group_content_uids(member_uids, child_uids)

        group = VisualGroup(
            uid=uuid.uuid4().hex,
            name=self._make_unique_group_name(name or "Group"),
            members=member_uids,
            parent_uid=parent_uid,
            layout=self._compute_group_layout(member_uids, child_uids),
            boundary_ports=self._build_group_boundary_ports(content_uids),
            child_group_uids=child_uids,
            member_layouts=self._capture_member_layouts(member_uids),
        )
        self.ensure_group_boundary_proxies(group)
        self.project_state.visual_groups.append(group)
        self._apply_group_creation_side_effects(group)
        return group

    def _group_content_uids(
        self,
        member_uids: list[str],
        child_group_uids: list[str] | None = None,
    ) -> list[str]:
        """Return all block uids contained in a group selection."""
        content: set[str] = set(member_uids)
        for child_uid in child_group_uids or []:
            child = self.project_state.get_visual_group(child_uid)
            if child is None:
                continue
            content.update(self._group_content_uids(child.members, child.child_group_uids))
        return list(content)

    def _group_content_uids_for_group(self, group: VisualGroup) -> list[str]:
        """Return all block uids owned by a group and its descendants."""
        return self._group_content_uids(group.members, group.child_group_uids)

    def _apply_group_creation_side_effects(self, group: VisualGroup) -> None:
        """Link a newly created group to its parent and child groups."""
        self._attach_group_to_parent(group)
        if group.parent_uid:
            parent = self.project_state.get_visual_group(group.parent_uid)
            if parent is not None:
                moved_uids = set(group.members)
                if moved_uids.intersection(parent.members):
                    parent.members = [
                        uid for uid in parent.members if uid not in moved_uids
                    ]
                    self._rebuild_group_boundary_ports(parent)
        for child_uid in group.child_group_uids:
            self._reparent_child_group(child_uid, group.uid)

    def _attach_group_to_parent(self, group: VisualGroup) -> None:
        """Register a new group under its parent container."""
        if not group.parent_uid:
            return
        parent = self.project_state.get_visual_group(group.parent_uid)
        if parent is None:
            group.parent_uid = None
            return
        if group.uid not in parent.child_group_uids:
            parent.child_group_uids.append(group.uid)

    def _reparent_child_group(self, child_uid: str, new_parent_uid: str) -> None:
        """Move a child group under a new parent group."""
        child = self.project_state.get_visual_group(child_uid)
        if child is None:
            return
        old_parent_uid = child.parent_uid
        if old_parent_uid and old_parent_uid != new_parent_uid:
            old_parent = self.project_state.get_visual_group(old_parent_uid)
            if old_parent is not None:
                old_parent.child_group_uids = [
                    uid for uid in old_parent.child_group_uids if uid != child_uid
                ]
        child.parent_uid = new_parent_uid

    def _detach_group_from_parent(self, group: VisualGroup) -> None:
        """Remove a group from its parent's child list."""
        if not group.parent_uid:
            return
        parent = self.project_state.get_visual_group(group.parent_uid)
        if parent is None:
            return
        parent.child_group_uids = [
            uid for uid in parent.child_group_uids if uid != group.uid
        ]

    def _promote_child_groups(self, group: VisualGroup) -> None:
        """Reparent child groups to the dissolved group's parent."""
        grandparent_uid = group.parent_uid
        for child_uid in list(group.child_group_uids):
            child = self.project_state.get_visual_group(child_uid)
            if child is None:
                continue
            child.parent_uid = grandparent_uid
            if grandparent_uid:
                grandparent = self.project_state.get_visual_group(grandparent_uid)
                if grandparent is not None and child_uid not in grandparent.child_group_uids:
                    grandparent.child_group_uids.append(child_uid)

    def _block_at_view_level(self, block_uid: str, view_group_uid: str | None) -> bool:
        """Return whether a block is a direct member of the active view level."""
        owner = self._group_containing_member(block_uid)
        if view_group_uid is None:
            return owner is None
        return owner is not None and owner.uid == view_group_uid

    def _group_exposing_boundary_for_block(
        self,
        block_uid: str,
        view_group_uid: str | None,
    ) -> VisualGroup | None:
        """Return the group whose border should expose a member port at this view level."""
        group = self._group_containing_member(block_uid)
        if group is None:
            return None
        while group.parent_uid != view_group_uid:
            if group.parent_uid is None:
                return group if view_group_uid is None else None
            parent = self.project_state.get_visual_group(group.parent_uid)
            if parent is None:
                return None
            group = parent
        return group

    def _remove_visual_group(self, group_uid: str) -> bool:
        """Remove a visual group without pushing undo."""
        return self.project_state.remove_visual_group(group_uid)

    def _collect_group_delete_targets(
        self, group_uid: str
    ) -> tuple[list[str], list[str]]:
        """Return nested group uids (children first) and all member block uids."""
        group = self.project_state.get_visual_group(group_uid)
        if group is None:
            return [], []
        group_uids: list[str] = []
        block_uids: list[str] = []
        for child_uid in group.child_group_uids:
            child_groups, child_blocks = self._collect_group_delete_targets(child_uid)
            group_uids.extend(child_groups)
            block_uids.extend(child_blocks)
        block_uids.extend(group.members)
        group_uids.append(group_uid)
        return group_uids, block_uids

    def _delete_group(self, group_uid: str) -> None:
        """Delete a visual group, its descendants, and all member blocks."""
        group = self.project_state.get_visual_group(group_uid)
        if group is None:
            return
        if group_uid in self.view.view_stack:
            self.view.navigate_out_of_group(group_uid)
        for child_uid in list(group.child_group_uids):
            self._delete_group(child_uid)
        for member_uid in list(group.members):
            block = self._find_block_by_uid(member_uid)
            if block is not None:
                self._remove_block(block)
        self._remove_visual_group(group_uid)
        self.view.refresh_visual_groups()

    def _group_containing_member(self, block_uid: str) -> VisualGroup | None:
        """Return the visual group that lists ``block_uid`` as a member."""
        for group in self.project_state.visual_groups:
            if block_uid in group.members:
                return group
        return None

    def _can_add_block_to_group(self, group_uid: str, block_uid: str) -> bool:
        if self._find_block_by_uid(block_uid) is None:
            return False
        group = self.project_state.get_visual_group(group_uid)
        if group is None or block_uid in group.members:
            return False
        owner = self._group_containing_member(block_uid)
        return owner is None or owner.uid == group_uid

    def _apply_group_snapshot(self, snapshot: dict | None, group_uid: str) -> None:
        """Restore a visual group from a serialized snapshot."""
        if snapshot is None:
            if group_uid in self.view.view_stack:
                self.view.navigate_out_of_group(group_uid)
            self._remove_visual_group(group_uid)
        else:
            group = VisualGroup.from_dict(snapshot)
            replaced = False
            for index, existing in enumerate(self.project_state.visual_groups):
                if existing.uid == group.uid:
                    self.project_state.visual_groups[index] = group
                    replaced = True
                    break
            if not replaced:
                self.project_state.visual_groups.append(group)
            self.ensure_group_boundary_proxies(group)
        self.view.refresh_visual_groups()

    def _add_member_to_group(
        self,
        group_uid: str,
        block_uid: str,
        layout: dict[str, Any],
    ) -> bool:
        group = self.project_state.get_visual_group(group_uid)
        if group is None or not self._can_add_block_to_group(group_uid, block_uid):
            return False

        group.members.append(block_uid)
        group.member_layouts[block_uid] = dict(layout)
        self._rebuild_group_boundary_ports(group)
        self.view.refresh_visual_groups()
        return True

    def _remove_boundaries_for_member(self, group: VisualGroup, block_uid: str) -> None:
        """Remove boundary ports tied to a member block."""
        prefix = f"{block_uid}:"
        for boundary in list(group.boundary_ports):
            if not boundary.linked_port_uid.startswith(prefix):
                continue
            connection = find_connection_for_boundary(self.project_state, boundary)
            if connection is not None:
                self._remove_connection(connection, refresh_boundaries=False)
        group.boundary_ports = [
            port
            for port in group.boundary_ports
            if not port.linked_port_uid.startswith(prefix)
        ]

    def _remove_member_from_group(self, group_uid: str, block_uid: str) -> bool:
        group = self.project_state.get_visual_group(group_uid)
        if group is None or block_uid not in group.members:
            return False

        layout = dict(group.member_layouts.get(block_uid, {}))
        self._remove_boundaries_for_member(group, block_uid)
        group.members = [uid for uid in group.members if uid != block_uid]
        group.member_layouts.pop(block_uid, None)

        if not group.members and not group.child_group_uids:
            if group_uid in self.view.view_stack:
                self.view.navigate_out_of_group(group_uid)
            self._remove_visual_group(group_uid)
        else:
            self._rebuild_group_boundary_ports(group)
            block = self._find_block_by_uid(block_uid)
            if block is not None and layout:
                item = self.view.get_block_item_from_instance(block)
                if item is not None:
                    self._apply_block_layout(item, layout)

        self.view.refresh_visual_groups()
        return True

    def _capture_member_layouts(self, member_uids: list[str]) -> dict[str, dict[str, Any]]:
        """Snapshot block item geometry for internal group view."""
        layouts: dict[str, dict[str, Any]] = {}
        for uid in member_uids:
            block = self._find_block_by_uid(uid)
            if block is None:
                continue
            item = self.view.get_block_item_from_instance(block)
            if item is None:
                continue
            layouts[uid] = self._capture_block_layout(block)
        return layouts

    def _apply_block_layout(self, block_item, layout: dict[str, Any]) -> None:
        """Apply a stored layout snapshot to a block item."""
        block_item.setPos(QPointF(float(layout.get("x", 0.0)), float(layout.get("y", 0.0))))
        block_item.setRect(
            0,
            0,
            float(layout.get("width", block_item.rect().width())),
            float(layout.get("height", block_item.rect().height())),
        )
        orientation = layout.get("orientation")
        if isinstance(orientation, str):
            block_item.orientation = orientation
        block_item._layout_ports()
        self.view.on_block_moved(block_item)

    def apply_member_layouts(self, group: VisualGroup) -> None:
        """Apply stored member layouts to visible block items."""
        for uid in group.members:
            layout = group.member_layouts.get(uid)
            if not layout:
                continue
            block = self._find_block_by_uid(uid)
            if block is None:
                continue
            item = self.view.get_block_item_from_instance(block)
            if item is None:
                continue
            self._apply_block_layout(item, layout)

    def save_member_layouts(self, group: VisualGroup) -> None:
        """Persist current block item geometry into the group model."""
        for uid in group.members:
            block = self._find_block_by_uid(uid)
            if block is None:
                continue
            item = self.view.get_block_item_from_instance(block)
            if item is None:
                continue
            group.member_layouts[uid] = self._capture_block_layout(block)

    def restore_members_after_ungroup(self, group: VisualGroup) -> None:
        """Place ungrouped members and promote child groups to the parent level."""
        self._promote_child_groups(group)
        self._detach_group_from_parent(group)
        self.apply_member_layouts(group)

    def ensure_group_boundary_proxies(self, group: VisualGroup) -> None:
        """Assign proxy ids and default layouts for each group boundary port."""
        inputs = [port for port in group.boundary_ports if port.direction == "input"]
        outputs = [port for port in group.boundary_ports if port.direction == "output"]
        for index, port in enumerate(inputs):
            self._ensure_boundary_proxy(port, "input", index, len(inputs), group)
        for index, port in enumerate(outputs):
            self._ensure_boundary_proxy(port, "output", index, len(outputs), group)

    def _ensure_boundary_proxy(
        self,
        boundary: BoundaryPort,
        direction: str,
        index: int,
        total: int,
        group: VisualGroup,
    ) -> None:
        if not boundary.proxy_uid:
            boundary.proxy_uid = uuid.uuid4().hex
        if not boundary.proxy_layout:
            boundary.proxy_layout = self._default_proxy_layout(
                direction, index, total, group
            )

    def _default_proxy_layout(
        self,
        direction: str,
        index: int,
        total: int,
        group: VisualGroup,
    ) -> dict[str, float]:
        layout = group.layout or {}
        height = float(layout.get("height", 100.0))
        y = 20.0 + (index + 1) * max(40.0, height / (total + 1))
        if direction == "input":
            return {"x": 10.0, "y": y}
        width = float(layout.get("width", 160.0))
        return {"x": max(80.0, width - 66.0), "y": y}

    def _apply_connection_route(
        self,
        connection: ConnectionInstance,
        points: list[QPointF] | None,
    ) -> None:
        connection_item = self.view.connections.get(connection)
        if connection_item is None:
            return
        if points is None or len(points) < 2:
            connection_item.invalidate_manual_route()
        else:
            connection_item.apply_manual_route(points)
        connection_item.update_position()

    def save_proxy_layouts(self, group: VisualGroup) -> None:
        """Persist current proxy item positions into the group model."""
        for boundary in group.boundary_ports:
            item = self.view.proxy_items.get(boundary.uid)
            if item is None:
                continue
            pos = item.pos()
            boundary.proxy_layout = {
                "x": float(pos.x()),
                "y": float(pos.y()),
                "orientation": item.orientation,
            }

    def _add_manual_boundary_port(
        self,
        group_uid: str,
        boundary: BoundaryPort,
    ) -> None:
        group = self.project_state.get_visual_group(group_uid)
        if group is None:
            return
        if any(port.uid == boundary.uid for port in group.boundary_ports):
            return
        group.boundary_ports.append(boundary)
        self.ensure_group_boundary_proxies(group)
        self.view.refresh_visual_groups()

    def _restore_boundary_port(
        self,
        group_uid: str,
        boundary: BoundaryPort,
        wiring: BoundaryWiringState,
        connection_snapshot: ConnectionSnapshot | None,
    ) -> None:
        group = self.project_state.get_visual_group(group_uid)
        if group is None:
            return
        if any(port.uid == boundary.uid for port in group.boundary_ports):
            return
        restored = BoundaryPort.from_dict(boundary.to_dict())
        apply_wiring_state(restored, wiring)
        group.boundary_ports.append(restored)
        self.ensure_group_boundary_proxies(group)
        if connection_snapshot is not None:
            connection = self._add_connection_from_snapshot(connection_snapshot)
            if connection is not None:
                restored.linked_connection_uid = self._connection_key(connection)
        self.view.refresh_visual_groups()

    def _remove_boundary_port(self, group_uid: str, boundary_uid: str) -> None:
        group = self.project_state.get_visual_group(group_uid)
        if group is None:
            return
        boundary = self._find_boundary_port(group, boundary_uid)
        if boundary is not None:
            connection = find_connection_for_boundary(self.project_state, boundary)
            if connection is not None:
                self._remove_connection(connection, refresh_boundaries=False)
        group.boundary_ports = [
            port for port in group.boundary_ports if port.uid != boundary_uid
        ]
        proxy_item = self.view.proxy_items.pop(boundary_uid, None)
        if proxy_item is not None:
            self.view.diagram_scene.removeItem(proxy_item)
        self.view.refresh_visual_groups()

    def _set_proxy_layout(
        self,
        group_uid: str,
        boundary_uid: str,
        pos: QPointF,
    ) -> None:
        group = self.project_state.get_visual_group(group_uid)
        if group is None:
            return
        boundary = next(
            (port for port in group.boundary_ports if port.uid == boundary_uid),
            None,
        )
        if boundary is None:
            return
        layout = dict(boundary.proxy_layout or {})
        layout["x"] = float(pos.x())
        layout["y"] = float(pos.y())
        boundary.proxy_layout = layout
        proxy_item = self.view.proxy_items.get(boundary_uid)
        if proxy_item is not None:
            proxy_item.setPos(QPointF(pos))
        for conn_item in self.view.connections.values():
            conn_item.update_position()

    def _set_boundary_label(self, group_uid: str, boundary_uid: str, label: str) -> None:
        group = self.project_state.get_visual_group(group_uid)
        if group is None:
            return
        boundary = self._find_boundary_port(group, boundary_uid)
        if boundary is None:
            return
        trimmed = label.strip()
        if not trimmed and boundary.origin == "manual":
            trimmed = self._make_unique_boundary_label(
                group,
                boundary.direction,
                exclude_uid=boundary_uid,
            )
        boundary.label = trimmed
        self.view.refresh_visual_groups()

    def _proxy_default_label(self, direction: str) -> str:
        return "In" if direction == "input" else "Out"

    def _make_unique_boundary_label(
        self,
        group: VisualGroup,
        direction: str,
        *,
        exclude_uid: str | None = None,
    ) -> str:
        """Return a unique default GroupIn/GroupOut name inside one group."""
        base = self._proxy_default_label(direction)
        used: set[str] = set()
        for port in group.boundary_ports:
            if port.uid == exclude_uid or port.origin != "manual":
                continue
            if port.direction != direction:
                continue
            name = port.label.strip() or self._proxy_default_label(port.direction)
            used.add(name)
        if base not in used:
            return base
        index = 1
        while f"{base}_{index}" in used:
            index += 1
        return f"{base}_{index}"

    def add_manual_boundary_port(
        self,
        group_uid: str,
        direction: str,
        pos: QPointF,
    ) -> BoundaryPort | None:
        """Add a manual GroupIn/GroupOut boundary port to a visual group."""
        group = self.project_state.get_visual_group(group_uid)
        if group is None:
            return None
        boundary = BoundaryPort(
            uid=uuid.uuid4().hex,
            direction=direction,
            origin="manual",
            label=self._make_unique_boundary_label(group, direction),
            proxy_uid=uuid.uuid4().hex,
            proxy_layout={"x": float(pos.x()), "y": float(pos.y())},
        )
        self.undo_manager.push(AddManualBoundaryCommand(self, group_uid, boundary))
        return boundary

    def remove_boundary_port(self, group_uid: str, boundary_uid: str) -> bool:
        """Remove a GroupIn/GroupOut boundary port (undoable)."""
        group = self.project_state.get_visual_group(group_uid)
        if group is None:
            return False
        boundary = self._find_boundary_port(group, boundary_uid)
        if boundary is None:
            return False
        self.undo_manager.push(
            RemoveBoundaryPortCommand(self, group_uid, boundary_uid)
        )
        return True

    def disconnect_manual_boundary_side(
        self,
        group_uid: str,
        boundary_uid: str,
        side: str,
    ) -> bool:
        """Disconnect one side of an incomplete manual boundary wire (undoable)."""
        group = self.project_state.get_visual_group(group_uid)
        if group is None:
            return False
        boundary = self._find_boundary_port(group, boundary_uid)
        if boundary is None or boundary.linked_connection_uid:
            return False
        if side not in ("internal", "external"):
            return False

        before = self._capture_boundary_wire_snapshot(group_uid, boundary_uid)
        after_wiring = capture_wiring_state(boundary)
        if side == "internal":
            if not after_wiring.linked_port_uid:
                return False
            after_wiring.linked_port_uid = ""
        else:
            if not after_wiring.external_port_uid:
                return False
            after_wiring.external_port_uid = ""
        after_wiring.linked_connection_uid = ""
        self.undo_manager.push(
            WireManualBoundaryCommand(
                self,
                group_uid,
                boundary_uid,
                before,
                (after_wiring, None),
            )
        )
        return True

    def remove_manual_boundary_port(self, group_uid: str, boundary_uid: str) -> bool:
        """Remove a manual GroupIn/GroupOut boundary port (undoable)."""
        return self.remove_boundary_port(group_uid, boundary_uid)

    def _compute_group_layout(
        self,
        member_uids: list[str],
        child_group_uids: list[str] | None = None,
    ) -> dict[str, float]:
        """Compute a bounding layout for group members and child groups."""
        margin = 16.0
        min_x = float("inf")
        min_y = float("inf")
        max_x = float("-inf")
        max_y = float("-inf")
        found = False

        for uid in member_uids:
            block = self._find_block_by_uid(uid)
            if block is None:
                continue
            item = self.view.get_block_item_from_instance(block)
            if item is None:
                continue
            found = True
            rect = item.sceneBoundingRect()
            min_x = min(min_x, rect.left())
            min_y = min(min_y, rect.top())
            max_x = max(max_x, rect.right())
            max_y = max(max_y, rect.bottom())

        for child_uid in child_group_uids or []:
            item = self.view.group_items.get(child_uid)
            if item is None:
                continue
            found = True
            rect = item.sceneBoundingRect()
            min_x = min(min_x, rect.left())
            min_y = min(min_y, rect.top())
            max_x = max(max_x, rect.right())
            max_y = max(max_y, rect.bottom())

        if not found:
            return {"x": 0.0, "y": 0.0, "width": 160.0, "height": 100.0}

        return {
            "x": float(min_x - margin),
            "y": float(min_y - margin),
            "width": float(max(max_x - min_x + 2 * margin, 80.0)),
            "height": float(max(max_y - min_y + 2 * margin, 50.0)),
        }

    def _build_group_boundary_ports(self, member_uids: list[str]) -> list[BoundaryPort]:
        """Derive boundary ports from connections crossing group boundaries."""
        members = set(member_uids)
        boundary_ports: list[BoundaryPort] = []
        by_internal_port_uid: dict[tuple[str, str], BoundaryPort] = {}

        for connection in self.project_state.connections:
            src_in = connection.src_block().uid in members
            dst_in = connection.dst_block().uid in members
            if src_in == dst_in:
                continue

            if dst_in:
                direction = "input"
                internal_port = connection.dst_port
            else:
                direction = "output"
                internal_port = connection.src_port

            key = (internal_port.block.uid, internal_port.name)
            if key in by_internal_port_uid:
                continue

            boundary = BoundaryPort(
                uid=uuid.uuid4().hex,
                direction=direction,
                linked_port_uid=f"{internal_port.block.uid}:{internal_port.name}",
                origin="auto",
                linked_connection_uid=self._connection_key(connection),
            )
            by_internal_port_uid[key] = boundary
            boundary_ports.append(boundary)

        return boundary_ports

    def _connection_key(self, connection: ConnectionInstance) -> str:
        """Build a stable key for one diagram connection."""
        from pySimBlocks.gui.services.group_boundary_service import connection_key

        return connection_key(connection)

    def _remove_auto_boundaries_for_member_port(
        self,
        group: VisualGroup,
        member_port_key: str,
        *,
        keep_uid: str | None = None,
    ) -> None:
        """Drop auto boundary ports superseded by a manual port on the same member."""
        group.boundary_ports = [
            port
            for port in group.boundary_ports
            if not (
                port.origin == "auto"
                and port.linked_port_uid == member_port_key
                and port.uid != keep_uid
            )
        ]

    def _rebuild_group_boundary_ports(self, group: VisualGroup) -> None:
        """Recompute auto boundary ports, keeping manual ports and stable auto ids."""
        manual_ports = [port for port in group.boundary_ports if port.origin == "manual"]
        manual_member_keys = {
            port.linked_port_uid
            for port in manual_ports
            if port.linked_port_uid
        }
        existing_auto = {
            port.linked_port_uid: port
            for port in group.boundary_ports
            if port.origin == "auto"
        }

        rebuilt_auto: list[BoundaryPort] = []
        for port in self._build_group_boundary_ports(
            self._group_content_uids_for_group(group)
        ):
            if port.linked_port_uid in manual_member_keys:
                continue
            previous = existing_auto.get(port.linked_port_uid)
            if previous is not None:
                port.uid = previous.uid
                port.proxy_uid = previous.proxy_uid
                port.proxy_layout = dict(previous.proxy_layout)
                port.external_port_uid = previous.external_port_uid
                if previous.linked_port_uid:
                    port.linked_port_uid = previous.linked_port_uid
                if not port.linked_connection_uid:
                    port.linked_connection_uid = previous.linked_connection_uid
            rebuilt_auto.append(port)

        rebuilt_keys = {port.linked_port_uid for port in rebuilt_auto}
        rebuilt_connection_keys = {
            port.linked_connection_uid
            for port in rebuilt_auto
            if port.linked_connection_uid
        }
        for port in group.boundary_ports:
            if port.origin != "auto":
                continue
            if port.linked_connection_uid:
                continue
            if not port.linked_port_uid and not port.external_port_uid:
                continue
            if port.linked_port_uid in manual_member_keys:
                continue
            if port.linked_port_uid and port.linked_port_uid in rebuilt_keys:
                continue
            if (
                not port.linked_port_uid
                and port.external_port_uid
                and any(
                    port.external_port_uid.split(":", 1)[0] in key
                    for key in rebuilt_connection_keys
                )
            ):
                continue
            rebuilt_auto.append(port)

        previous_auto_order = [
            port.linked_port_uid
            for port in group.boundary_ports
            if port.origin == "auto" and port.linked_port_uid
        ]

        def _auto_boundary_order(port: BoundaryPort) -> tuple[int, str]:
            try:
                return (previous_auto_order.index(port.linked_port_uid), port.uid)
            except ValueError:
                return (len(previous_auto_order), port.linked_port_uid or port.uid)

        rebuilt_auto.sort(key=_auto_boundary_order)
        group.boundary_ports = manual_ports + rebuilt_auto
        self.ensure_group_boundary_proxies(group)

    def _group_needs_boundary_refresh(
        self,
        group: VisualGroup,
        block_uids: set[str],
    ) -> bool:
        """Return whether a group may need boundary ports recomputed."""
        members = set(self._group_content_uids_for_group(group))
        if members.intersection(block_uids):
            return True

        for uid in block_uids:
            prefix = f"{uid}:"
            for port in group.boundary_ports:
                if port.linked_port_uid.startswith(prefix):
                    return True
                if port.external_port_uid.startswith(prefix):
                    return True

        for connection in self.project_state.connections:
            src_uid = connection.src_block().uid
            dst_uid = connection.dst_block().uid
            src_in = src_uid in members
            dst_in = dst_uid in members
            if src_in != dst_in and (src_uid in block_uids or dst_uid in block_uids):
                return True
        return False

    def _group_has_stale_boundaries(self, group: VisualGroup) -> bool:
        """Return whether auto boundaries no longer match project connections."""
        members = set(self._group_content_uids_for_group(group))
        connection_keys = {
            self._connection_key(connection)
            for connection in self.project_state.connections
        }
        for port in group.boundary_ports:
            if port.origin == "manual":
                continue
            if port.linked_port_uid:
                block_uid = port.linked_port_uid.split(":", 1)[0]
                if block_uid not in members or self._find_block_by_uid(block_uid) is None:
                    return True
            if port.linked_connection_uid and port.linked_connection_uid not in connection_keys:
                return True
        return False

    def _refresh_boundaries_for_member_uids(self, block_uids: set[str]) -> None:
        """Refresh boundary ports for groups affected by block or connection changes."""
        changed = False
        for group in self.project_state.visual_groups:
            if self._group_needs_boundary_refresh(
                group, block_uids
            ) or self._group_has_stale_boundaries(group):
                self._rebuild_group_boundary_ports(group)
                changed = True
        if changed:
            self.view.refresh_visual_groups()

    def _make_unique_group_name(
        self,
        base_name: str,
        exclude_uid: str | None = None,
    ) -> str:
        """Return a unique visual group name based on existing groups."""
        existing = {
            g.name
            for g in self.project_state.visual_groups
            if g.uid != exclude_uid
        }
        if base_name not in existing:
            return base_name
        i = 1
        while f"{base_name}_{i}" in existing:
            i += 1
        return f"{base_name}_{i}"
