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

from dataclasses import dataclass
from typing import Any

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QUndoCommand

from pySimBlocks.gui.models import BlockInstance, PortInstance


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

    def redo(self) -> None:
        if self._connection_instance is not None:
            self._controller._remove_connection(self._connection_instance)
            self._controller.make_dirty()

    def undo(self) -> None:
        self._connection_instance = self._controller._add_connection_from_snapshot(self._snapshot)
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
        self._plots_before = [dict(title=p["title"], signals=list(p["signals"])) for p in controller.project_state.plots]

    def redo(self) -> None:
        self._controller._remove_block(self._block_instance)
        self._controller.make_dirty()

    def undo(self) -> None:
        self._controller._add_block(self._block_instance, self._layout)
        for snapshot in self._connections:
            self._controller._add_connection_from_snapshot(snapshot)
        self._controller.project_state.logging = list(self._logging_before)
        self._controller.project_state.plots = [dict(title=p["title"], signals=list(p["signals"])) for p in self._plots_before]
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
