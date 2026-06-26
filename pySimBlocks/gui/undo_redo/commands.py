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
from dataclasses import dataclass
from typing import Any

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QUndoCommand

from pySimBlocks.gui.models import BlockInstance, ConnectionInstance, PortInstance, VisualGroup
from pySimBlocks.gui.models.visual_group import BoundaryPort


def _clone_route_points(points: list[QPointF] | None) -> list[QPointF] | None:
    if points is None:
        return None
    return [QPointF(point) for point in points]


def routes_equal(
    left: list[QPointF] | None,
    right: list[QPointF] | None,
) -> bool:
    if left is None and right is None:
        return True
    if left is None or right is None:
        return False
    if len(left) != len(right):
        return False
    return all(
        left_point.x() == right_point.x() and left_point.y() == right_point.y()
        for left_point, right_point in zip(left, right)
    )


@dataclass
class ConnectionSnapshot:
    src_block_uid: str
    src_port_name: str
    dst_block_uid: str
    dst_port_name: str
    points: list[QPointF] | None = None


class AddBlockCommand(QUndoCommand):
    def __init__(self, controller, block_instance: BlockInstance, block_layout: dict | None = None):
        super().__init__("Add Block")
        self._controller = controller
        self._block_instance = block_instance
        self._block_layout = dict(block_layout or {})

    def redo(self) -> None:
        self._controller._add_block(self._block_instance, self._block_layout)
        self._controller.make_dirty()

    def undo(self) -> None:
        self._controller._remove_block(self._block_instance)
        self._controller.make_dirty()


class AddConnectionCommand(QUndoCommand):
    def __init__(self, controller, src_port: PortInstance, dst_port: PortInstance, points: list[QPointF] | None = None):
        super().__init__("Add Connection")
        self._controller = controller
        self._snapshot = ConnectionSnapshot(
            src_block_uid=src_port.block.uid,
            src_port_name=src_port.name,
            dst_block_uid=dst_port.block.uid,
            dst_port_name=dst_port.name,
            points=list(points) if points else None,
        )
        self._connection_instance = None

    def redo(self) -> None:
        self._connection_instance = self._controller._add_connection_from_snapshot(self._snapshot)
        self._controller.make_dirty()

    def undo(self) -> None:
        if self._connection_instance is not None:
            self._controller._remove_connection(self._connection_instance)
            self._controller.make_dirty()


class RemoveConnectionCommand(QUndoCommand):
    def __init__(self, controller, connection_instance):
        super().__init__("Delete Connection")
        self._controller = controller
        self._snapshot = controller._capture_connection_snapshot(connection_instance)
        self._connection_instance = connection_instance
        self._boundary_snapshots = controller._capture_boundaries_for_connection(
            connection_instance
        )

    def redo(self) -> None:
        if self._connection_instance is not None:
            self._controller._remove_connection(self._connection_instance)
            self._controller.make_dirty()

    def undo(self) -> None:
        self._connection_instance = self._controller._add_connection_from_snapshot(
            self._snapshot,
            refresh_boundaries=False,
        )
        self._controller._restore_boundary_snapshots(self._boundary_snapshots)
        self._controller.make_dirty()


class RemoveBlockCommand(QUndoCommand):
    def __init__(self, controller, block_instance: BlockInstance):
        super().__init__("Delete Block")
        self._controller = controller
        self._block_instance = block_instance
        self._layout = controller._capture_block_layout(block_instance)
        self._connections = [
            controller._capture_connection_snapshot(connection)
            for connection in controller.project_state.get_connections_of_block(block_instance)
        ]
        self._logging_before = list(controller.project_state.logging)
        self._plots_before = copy.deepcopy(controller.project_state.plots)
        self._group_snapshots = {
            group.uid: group.to_dict()
            for group in controller.project_state.visual_groups
            if block_instance.uid in group.members
        }

    def redo(self) -> None:
        self._controller._remove_block(self._block_instance)
        self._controller.make_dirty()

    def undo(self) -> None:
        self._controller._add_block(self._block_instance, self._layout)
        for snapshot in self._connections:
            self._controller._add_connection_from_snapshot(snapshot)
        self._controller.project_state.logging = list(self._logging_before)
        self._controller.project_state.plots = copy.deepcopy(self._plots_before)
        for group_uid, group_snapshot in self._group_snapshots.items():
            self._controller._apply_group_snapshot(group_snapshot, group_uid)
            group = self._controller.project_state.get_visual_group(group_uid)
            if group is not None:
                self._controller.apply_member_layouts(group)
        self._controller.make_dirty()


class MoveResizeBlockCommand(QUndoCommand):
    def __init__(self, controller, block_uid: str, old_pos: QPointF, old_rect: QRectF, new_pos: QPointF, new_rect: QRectF):
        super().__init__("Move/Resize Block")
        self._controller = controller
        self._block_uid = block_uid
        self._old_pos = QPointF(old_pos)
        self._old_rect = QRectF(old_rect)
        self._new_pos = QPointF(new_pos)
        self._new_rect = QRectF(new_rect)

    def redo(self) -> None:
        self._controller._set_block_geometry(self._block_uid, self._new_pos, self._new_rect)
        self._controller.make_dirty()

    def undo(self) -> None:
        self._controller._set_block_geometry(self._block_uid, self._old_pos, self._old_rect)
        self._controller.make_dirty()


class ToggleOrientationCommand(QUndoCommand):
    def __init__(self, controller, block_uid: str, old_orientation: str, new_orientation: str):
        super().__init__("Flip Block")
        self._controller = controller
        self._block_uid = block_uid
        self._old_orientation = old_orientation
        self._new_orientation = new_orientation

    def redo(self) -> None:
        self._controller._set_block_orientation(self._block_uid, self._new_orientation)
        self._controller.make_dirty()

    def undo(self) -> None:
        self._controller._set_block_orientation(self._block_uid, self._old_orientation)
        self._controller.make_dirty()


class ToggleGroupOrientationCommand(QUndoCommand):
    def __init__(self, controller, group_uid: str, old_orientation: str, new_orientation: str):
        super().__init__("Flip Group")
        self._controller = controller
        self._group_uid = group_uid
        self._old_orientation = old_orientation
        self._new_orientation = new_orientation

    def redo(self) -> None:
        self._controller._set_group_orientation(self._group_uid, self._new_orientation)
        self._controller.make_dirty()

    def undo(self) -> None:
        self._controller._set_group_orientation(self._group_uid, self._old_orientation)
        self._controller.make_dirty()


class ToggleProxyOrientationCommand(QUndoCommand):
    def __init__(
        self,
        controller,
        group_uid: str,
        boundary_uid: str,
        old_orientation: str,
        new_orientation: str,
    ):
        super().__init__("Flip Proxy")
        self._controller = controller
        self._group_uid = group_uid
        self._boundary_uid = boundary_uid
        self._old_orientation = old_orientation
        self._new_orientation = new_orientation

    def redo(self) -> None:
        self._controller._set_proxy_orientation(
            self._group_uid, self._boundary_uid, self._new_orientation
        )
        self._controller.make_dirty()

    def undo(self) -> None:
        self._controller._set_proxy_orientation(
            self._group_uid, self._boundary_uid, self._old_orientation
        )
        self._controller.make_dirty()


class GroupBlocksCommand(QUndoCommand):
    def __init__(
        self,
        controller,
        blocks: list[BlockInstance],
        name: str | None = None,
        *,
        child_group_uids: list[str] | None = None,
        parent_uid: str | None = None,
    ):
        super().__init__("Group Blocks")
        self._controller = controller
        self._blocks = list(blocks)
        self._name = name
        self._child_group_uids = list(child_group_uids or [])
        self._parent_uid = parent_uid
        self._group_uid: str | None = None
        self._group_snapshot: dict | None = None
        self._child_snapshots_before: dict[str, dict] = {}
        self._parent_children_before: list[str] | None = None
        self._parent_snapshot_before: dict | None = None

    def redo(self) -> None:
        if self._group_snapshot is not None:
            group = VisualGroup.from_dict(self._group_snapshot)
            self._controller.project_state.visual_groups.append(group)
            self._group_uid = group.uid
            self._controller.ensure_group_boundary_proxies(group)
            self._controller._apply_group_creation_side_effects(group)
        else:
            for child_uid in self._child_group_uids:
                child = self._controller.project_state.get_visual_group(child_uid)
                if child is not None:
                    self._child_snapshots_before[child_uid] = child.to_dict()
            if self._parent_uid:
                parent = self._controller.project_state.get_visual_group(self._parent_uid)
                if parent is not None:
                    self._parent_children_before = list(parent.child_group_uids)
                    self._parent_snapshot_before = parent.to_dict()

            group = self._controller._create_visual_group(
                self._blocks,
                self._name,
                child_group_uids=self._child_group_uids,
                parent_uid=self._parent_uid,
            )
            self._group_uid = group.uid
            self._group_snapshot = group.to_dict()
        self._controller.view.refresh_visual_groups()
        self._controller.make_dirty()

    def undo(self) -> None:
        if not self._group_uid:
            return
        group = self._controller.project_state.get_visual_group(self._group_uid)
        if group is not None:
            self._group_snapshot = group.to_dict()
            self._controller._detach_group_from_parent(group)
        if self._group_uid in self._controller.view.view_stack:
            self._controller.view.navigate_out_of_group(self._group_uid)
        self._controller._remove_visual_group(self._group_uid)

        for child_uid, snapshot in self._child_snapshots_before.items():
            child = VisualGroup.from_dict(snapshot)
            replaced = False
            for index, existing in enumerate(self._controller.project_state.visual_groups):
                if existing.uid == child_uid:
                    self._controller.project_state.visual_groups[index] = child
                    replaced = True
                    break
            if not replaced:
                self._controller.project_state.visual_groups.append(child)

        if self._parent_uid and self._parent_children_before is not None:
            parent = self._controller.project_state.get_visual_group(self._parent_uid)
            if parent is not None:
                parent.child_group_uids = list(self._parent_children_before)

        if self._parent_snapshot_before is not None:
            parent = VisualGroup.from_dict(self._parent_snapshot_before)
            for index, existing in enumerate(self._controller.project_state.visual_groups):
                if existing.uid == parent.uid:
                    self._controller.project_state.visual_groups[index] = parent
                    break

        self._controller.view.refresh_visual_groups()
        self._controller.make_dirty()


class UngroupCommand(QUndoCommand):
    def __init__(self, controller, group_uid: str):
        super().__init__("Ungroup")
        self._controller = controller
        self._group_uid = group_uid
        self._group_snapshot: dict | None = None

    def redo(self) -> None:
        group = self._controller.project_state.get_visual_group(self._group_uid)
        if group is not None:
            self._group_snapshot = group.to_dict()
            if self._group_uid in self._controller.view.view_stack:
                self._controller.view.navigate_out_of_group(self._group_uid)
            self._controller.restore_members_after_ungroup(group)
            self._controller._remove_visual_group(self._group_uid)
            self._controller.view.refresh_visual_groups()
            self._controller.make_dirty()

    def undo(self) -> None:
        if self._group_snapshot:
            group = VisualGroup.from_dict(self._group_snapshot)
            self._controller.project_state.visual_groups.append(group)
        self._controller.view.refresh_visual_groups()
        self._controller.make_dirty()


class DeleteGroupCommand(QUndoCommand):
    def __init__(self, controller, group_uid: str):
        super().__init__("Delete Group")
        self._controller = controller
        self._root_group_uid = group_uid
        self._group_snapshots: dict[str, dict] = {}
        self._group_uids_order: list[str] = []
        self._members: list[tuple[BlockInstance, dict]] = []
        self._connections: list[ConnectionSnapshot] = []

        group_uids, block_uids = controller._collect_group_delete_targets(group_uid)
        self._group_uids_order = group_uids
        for uid in group_uids:
            group = controller.project_state.get_visual_group(uid)
            if group is not None:
                self._group_snapshots[uid] = group.to_dict()

        seen_blocks: set[str] = set()
        seen_connections: set[int] = set()
        for member_uid in block_uids:
            if member_uid in seen_blocks:
                continue
            seen_blocks.add(member_uid)
            block = controller._find_block_by_uid(member_uid)
            if block is None:
                continue
            self._members.append(
                (block, controller._capture_block_layout(block))
            )
            for connection in controller.project_state.get_connections_of_block(block):
                conn_id = id(connection)
                if conn_id in seen_connections:
                    continue
                seen_connections.add(conn_id)
                self._connections.append(
                    controller._capture_connection_snapshot(connection)
                )

        self._logging_before = list(controller.project_state.logging)
        self._plots_before = copy.deepcopy(controller.project_state.plots)

    def redo(self) -> None:
        self._controller._delete_group(self._root_group_uid)
        self._controller.make_dirty()

    def undo(self) -> None:
        for block, layout in self._members:
            self._controller._add_block(block, layout)
        for snapshot in self._connections:
            self._controller._add_connection_from_snapshot(snapshot)
        self._controller.project_state.logging = list(self._logging_before)
        self._controller.project_state.plots = copy.deepcopy(self._plots_before)
        for uid in self._group_uids_order:
            snapshot = self._group_snapshots.get(uid)
            if snapshot is not None:
                self._controller._apply_group_snapshot(snapshot, uid)
        for uid in self._group_uids_order:
            group = self._controller.project_state.get_visual_group(uid)
            if group is not None:
                self._controller.apply_member_layouts(group)
        self._controller.make_dirty()


class AddToGroupCommand(QUndoCommand):
    def __init__(
        self,
        controller,
        group_uid: str,
        block_uid: str,
        layout: dict[str, Any],
    ):
        super().__init__("Add to Group")
        self._controller = controller
        self._group_uid = group_uid
        self._block_uid = block_uid
        self._layout = dict(layout)
        group = controller.project_state.get_visual_group(group_uid)
        self._snapshot_before = group.to_dict() if group is not None else None
        self._snapshot_after: dict | None = None

    def redo(self) -> None:
        self._controller._add_member_to_group(
            self._group_uid, self._block_uid, self._layout
        )
        group = self._controller.project_state.get_visual_group(self._group_uid)
        if group is not None:
            self._snapshot_after = group.to_dict()
        self._controller.make_dirty()

    def undo(self) -> None:
        self._controller._apply_group_snapshot(self._snapshot_before, self._group_uid)
        self._controller.make_dirty()


class RemoveFromGroupCommand(QUndoCommand):
    def __init__(self, controller, group_uid: str, block_uid: str):
        super().__init__("Remove from Group")
        self._controller = controller
        self._group_uid = group_uid
        self._block_uid = block_uid
        group = controller.project_state.get_visual_group(group_uid)
        self._snapshot_before = group.to_dict() if group is not None else None
        self._snapshot_after: dict | None = None

    def redo(self) -> None:
        self._controller._remove_member_from_group(self._group_uid, self._block_uid)
        group = self._controller.project_state.get_visual_group(self._group_uid)
        self._snapshot_after = group.to_dict() if group is not None else None
        self._controller.make_dirty()

    def undo(self) -> None:
        self._controller._apply_group_snapshot(self._snapshot_before, self._group_uid)
        self._controller.make_dirty()


class MoveResizeGroupCommand(QUndoCommand):
    def __init__(
        self,
        controller,
        group_uid: str,
        old_pos: QPointF,
        old_rect: QRectF,
        new_pos: QPointF,
        new_rect: QRectF,
    ):
        super().__init__("Move/Resize Group")
        self._controller = controller
        self._group_uid = group_uid
        self._old_pos = QPointF(old_pos)
        self._old_rect = QRectF(old_rect)
        self._new_pos = QPointF(new_pos)
        self._new_rect = QRectF(new_rect)

    def redo(self) -> None:
        self._controller._set_group_geometry(self._group_uid, self._new_pos, self._new_rect)
        self._controller.make_dirty()

    def undo(self) -> None:
        self._controller._set_group_geometry(self._group_uid, self._old_pos, self._old_rect)
        self._controller.make_dirty()


class EditBlockParamsCommand(QUndoCommand):
    def __init__(self, controller, block_instance: BlockInstance, new_params: dict[str, Any]):
        super().__init__("Edit Block Parameters")
        self._controller = controller
        self._block_instance = block_instance
        self._old_name = block_instance.name
        self._old_params = dict(block_instance.parameters)
        self._new_name = new_params.get("name", block_instance.name)
        self._new_params = {k: v for k, v in new_params.items() if k != "name"}
        self._removed_connections: list[ConnectionSnapshot] = []

    def redo(self) -> None:
        self._removed_connections = self._controller._apply_block_update(
            self._block_instance,
            self._new_name,
            self._new_params,
        )
        self._controller.make_dirty()

    def undo(self) -> None:
        self._controller._apply_block_update(
            self._block_instance,
            self._old_name,
            self._old_params,
        )
        for snapshot in self._removed_connections:
            self._controller._add_connection_from_snapshot(snapshot)
        self._controller.make_dirty()


class EditConnectionRouteCommand(QUndoCommand):
    def __init__(
        self,
        controller,
        connection_instance: ConnectionInstance,
        old_points: list[QPointF] | None,
        new_points: list[QPointF] | None,
    ):
        super().__init__("Edit Connection Route")
        self._controller = controller
        self._connection_instance = connection_instance
        self._old_points = _clone_route_points(old_points)
        self._new_points = _clone_route_points(new_points)

    def redo(self) -> None:
        self._controller._apply_connection_route(
            self._connection_instance, self._new_points
        )
        self._controller.make_dirty()

    def undo(self) -> None:
        self._controller._apply_connection_route(
            self._connection_instance, self._old_points
        )
        self._controller.make_dirty()


class AddManualBoundaryCommand(QUndoCommand):
    def __init__(self, controller, group_uid: str, boundary: BoundaryPort):
        super().__init__("Add Group Port")
        self._controller = controller
        self._group_uid = group_uid
        self._boundary = boundary

    def redo(self) -> None:
        self._controller._add_manual_boundary_port(self._group_uid, self._boundary)
        self._controller.make_dirty()

    def undo(self) -> None:
        self._controller._remove_boundary_port(
            self._group_uid, self._boundary.uid
        )
        self._controller.make_dirty()


class RemoveBoundaryPortCommand(QUndoCommand):
    def __init__(self, controller, group_uid: str, boundary_uid: str):
        super().__init__("Remove Group Port")
        self._controller = controller
        self._group_uid = group_uid
        self._boundary_uid = boundary_uid
        group = controller.project_state.get_visual_group(group_uid)
        boundary = (
            controller._find_boundary_port(group, boundary_uid) if group is not None else None
        )
        self._boundary_snapshot = (
            BoundaryPort.from_dict(boundary.to_dict()) if boundary is not None else None
        )
        wiring, connection = controller._capture_boundary_wire_snapshot(
            group_uid, boundary_uid
        )
        self._wiring = wiring
        self._connection_snapshot = connection

    def redo(self) -> None:
        if self._boundary_snapshot is None:
            return
        self._controller._remove_boundary_port(self._group_uid, self._boundary_uid)
        self._controller.make_dirty()

    def undo(self) -> None:
        if self._boundary_snapshot is None:
            return
        self._controller._restore_boundary_port(
            self._group_uid,
            self._boundary_snapshot,
            self._wiring,
            self._connection_snapshot,
        )
        self._controller.make_dirty()


RemoveManualBoundaryCommand = RemoveBoundaryPortCommand


class MoveProxyLayoutCommand(QUndoCommand):
    def __init__(
        self,
        controller,
        group_uid: str,
        boundary_uid: str,
        old_pos: QPointF,
        new_pos: QPointF,
    ):
        super().__init__("Move Group Port")
        self._controller = controller
        self._group_uid = group_uid
        self._boundary_uid = boundary_uid
        self._old_pos = QPointF(old_pos)
        self._new_pos = QPointF(new_pos)

    def redo(self) -> None:
        self._controller._set_proxy_layout(
            self._group_uid, self._boundary_uid, self._new_pos
        )
        self._controller.make_dirty()

    def undo(self) -> None:
        self._controller._set_proxy_layout(
            self._group_uid, self._boundary_uid, self._old_pos
        )
        self._controller.make_dirty()


class RenameGroupCommand(QUndoCommand):
    def __init__(self, controller, group_uid: str, old_name: str, new_name: str):
        super().__init__("Rename Group")
        self._controller = controller
        self._group_uid = group_uid
        self._old_name = old_name
        self._new_name = new_name

    def redo(self) -> None:
        group = self._controller.project_state.get_visual_group(self._group_uid)
        if group is None:
            return
        group.name = self._new_name
        self._controller.view.refresh_visual_groups()
        self._controller.view.view_stack_changed.emit()
        self._controller.make_dirty()

    def undo(self) -> None:
        group = self._controller.project_state.get_visual_group(self._group_uid)
        if group is None:
            return
        group.name = self._old_name
        self._controller.view.refresh_visual_groups()
        self._controller.view.view_stack_changed.emit()
        self._controller.make_dirty()


class RenameBoundaryPortCommand(QUndoCommand):
    def __init__(
        self,
        controller,
        group_uid: str,
        boundary_uid: str,
        old_label: str,
        new_label: str,
    ):
        super().__init__("Rename Group Port")
        self._controller = controller
        self._group_uid = group_uid
        self._boundary_uid = boundary_uid
        self._old_label = old_label
        self._new_label = new_label

    def redo(self) -> None:
        self._controller._set_boundary_label(
            self._group_uid, self._boundary_uid, self._new_label
        )
        self._controller.make_dirty()

    def undo(self) -> None:
        self._controller._set_boundary_label(
            self._group_uid, self._boundary_uid, self._old_label
        )
        self._controller.make_dirty()


class WireManualBoundaryCommand(QUndoCommand):
    def __init__(
        self,
        controller,
        group_uid: str,
        boundary_uid: str,
        before: tuple,
        after: tuple,
    ):
        super().__init__("Wire Group Port")
        self._controller = controller
        self._group_uid = group_uid
        self._boundary_uid = boundary_uid
        self._before = before
        self._after = after

    def redo(self) -> None:
        wiring, connection = self._after
        self._controller._apply_boundary_wire_snapshot(
            self._group_uid, self._boundary_uid, wiring, connection
        )
        self._controller.make_dirty()

    def undo(self) -> None:
        wiring, connection = self._before
        self._controller._apply_boundary_wire_snapshot(
            self._group_uid, self._boundary_uid, wiring, connection
        )
        self._controller.make_dirty()


class PasteClipboardCommand(QUndoCommand):
    def __init__(
        self,
        controller,
        clipboard,
        origin: QPointF,
        parent_group_uid: str | None = None,
    ):
        super().__init__("Paste")
        self._controller = controller
        self._clipboard = clipboard
        self._origin = QPointF(origin)
        self._parent_group_uid = parent_group_uid
        self._result = None

    def redo(self) -> None:
        from pySimBlocks.gui.diagram_clipboard import paste_clipboard

        self._result = paste_clipboard(
            self._controller,
            self._clipboard,
            self._origin,
            parent_group_uid=self._parent_group_uid,
        )
        self._controller.make_dirty()

    def undo(self) -> None:
        from pySimBlocks.gui.diagram_clipboard import undo_paste

        if self._result is not None:
            undo_paste(self._controller, self._result)
            self._controller.make_dirty()
