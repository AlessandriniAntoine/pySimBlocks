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

from typing import TYPE_CHECKING, Any

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QGuiApplication, QKeySequence, QPainter, QPen
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView, QInputDialog, QMenu

from pySimBlocks.gui.graphics.block_item import BlockItem
from pySimBlocks.gui.graphics.group_item import GroupBoundaryPortItem, GroupItem
from pySimBlocks.gui.diagram_clipboard import DiagramClipboard, clipboard_has_content
from pySimBlocks.gui.graphics.group_proxy_item import GroupProxyItem, GroupProxyPortItem
from pySimBlocks.gui.graphics.connection_item import ConnectionItem, OrthogonalRoute
from pySimBlocks.gui.graphics.manual_boundary_wire_item import ManualBoundaryWireItem
from pySimBlocks.gui.graphics.port_item import PortItem
from pySimBlocks.gui.graphics.theme import make_theme
from pySimBlocks.gui.group_ports import GROUP_IN_TYPE, GROUP_OUT_TYPE, GROUP_PORTS_CATEGORY
from pySimBlocks.gui.models.block_instance import BlockInstance
from pySimBlocks.gui.models.connection_instance import ConnectionInstance
from pySimBlocks.gui.services.group_boundary_service import find_port

if TYPE_CHECKING:
    from pySimBlocks.gui.project_controller import ProjectController


class DiagramView(QGraphicsView):
    """Interactive Qt graphics view for the block diagram canvas."""

    group_view_changed = Signal()
    view_stack_changed = Signal()

    def __init__(self):
        """Initialize the diagram view and configure scene behavior.

        Args:
            None.

        Raises:
            None.
        """
        super().__init__()
        self.diagram_scene = QGraphicsScene(self)
        self.setScene(self.diagram_scene)
        self.setAcceptDrops(True)

        self.setRenderHint(QPainter.Antialiasing)
        self.theme = make_theme()
        self.diagram_scene.setBackgroundBrush(self.theme.scene_bg)
        hints = QGuiApplication.styleHints()
        hints.colorSchemeChanged.connect(self._on_color_scheme_changed)
        app = QGuiApplication.instance()
        if hasattr(app, "paletteChanged"):
            app.paletteChanged.connect(lambda *_: QTimer.singleShot(0, self._apply_theme_from_system))
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)

        self.pending_port: PortItem | GroupProxyPortItem | GroupBoundaryPortItem | None = None
        self.temp_connection: ConnectionItem | None = None
        self.clipboard: DiagramClipboard | None = None
        self.paste_generation = 0
        self.drop_event_pos: QPointF = QPointF(0, 0)
        self.project_controller: ProjectController | None
        self.block_items: dict[str, BlockItem] = {}
        self.group_items: dict[str, GroupItem] = {}
        self.proxy_items: dict[str, GroupProxyItem] = {}
        self.manual_boundary_wires: dict[str, ManualBoundaryWireItem] = {}
        self.connections: dict[ConnectionInstance, ConnectionItem] = {}
        self.view_stack: list[str] = []

        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.RubberBandDrag)

    # --------------------------------------------------------------------------
    # Public Methods
    # --------------------------------------------------------------------------

    def add_block(
        self,
        block_instance: BlockInstance,
        block_layout: dict[str, Any] | None = None,
    ) -> None:
        """Add a visual block item to the scene for the given block instance.

        Args:
            block_instance: The block model to represent visually.
            block_layout: Optional dict with position/size hints.
        """
        block_item = BlockItem(block_instance, self.drop_event_pos, self, block_layout)
        self.diagram_scene.addItem(block_item)
        self.block_items[block_instance.uid] = block_item

    def refresh_block_port(self, block_instance: BlockInstance) -> None:
        """Refresh the port visuals of the block item for the given instance.

        Args:
            block_instance: The block whose port items should be refreshed.
        """
        block_item = self.get_block_item_from_instance(block_instance)
        if block_item:
            block_item.refresh_ports()
            self._refresh_group_port_labels()

    def remove_block(self, block_instance: BlockInstance) -> None:
        """Remove the visual block item for the given instance from the scene.

        Args:
            block_instance: The block whose visual item should be removed.
        """
        block_item = self.block_items[block_instance.uid]
        self.diagram_scene.removeItem(block_item)
        self.block_items.pop(block_instance.uid, None)

    def add_connection(
        self,
        connection_instance: ConnectionInstance,
        points: list[QPointF] | None = None,
    ) -> None:
        """Add a visual wire to the scene for the given connection instance.

        Args:
            connection_instance: The connection model to represent visually.
            points: Optional list of intermediate waypoints for the wire.
        """
        src_port_item = self.get_block_item_from_instance(connection_instance.src_block()).get_port_item(connection_instance.src_port.name)
        dst_port_item = self.get_block_item_from_instance(connection_instance.dst_block()).get_port_item(connection_instance.dst_port.name)
        connection_item = ConnectionItem(
            src_port_item, dst_port_item, connection_instance, points
        )
        self.connections[connection_instance] = connection_item
        self.diagram_scene.addItem(connection_item)

    def remove_connection(self, connection_instance: ConnectionInstance) -> None:
        """Remove the visual wire for the given connection instance from the scene.

        Args:
            connection_instance: The connection whose visual item should be removed.
        """
        connection_item = self.connections.pop(connection_instance, None)
        if connection_item:
            self.diagram_scene.removeItem(connection_item)

    def get_selected_block_instances(self) -> list[BlockInstance]:
        """Return block instances currently selected on the diagram."""
        selected = []
        for item in self.diagram_scene.selectedItems():
            if isinstance(item, BlockItem) and item.isVisible():
                selected.append(item.instance)
        return selected

    def get_selected_group_uids(self) -> list[str]:
        """Return UIDs of all selected visible group items."""
        uids: list[str] = []
        for item in self.diagram_scene.selectedItems():
            if isinstance(item, GroupItem) and item.isVisible():
                uids.append(item.group.uid)
        return uids

    def get_selected_group_uid(self) -> str | None:
        """Return the UID of a selected group item, if any."""
        uids = self.get_selected_group_uids()
        return uids[0] if uids else None

    def group_item_for_block_drop(self, block_item: BlockItem) -> GroupItem | None:
        """Return the group under a block's center, for drag-and-drop membership."""
        if self.project_controller is None or self.current_view_group_uid is not None:
            return None
        center = block_item.sceneBoundingRect().center()
        for group_item in self.group_items.values():
            if not group_item.isVisible():
                continue
            if group_item.sceneBoundingRect().contains(center):
                return group_item
        return None

    def try_drop_block_onto_group(self, block_item: BlockItem) -> bool:
        """Add a root-level block to the group it was dropped onto."""
        if self.project_controller is None:
            return False
        target_group = self.group_item_for_block_drop(block_item)
        if target_group is None:
            return False
        layout = self.project_controller._capture_block_layout(block_item.instance)
        return self.project_controller.add_block_to_group(
            target_group.group.uid,
            block_item.instance,
            layout,
        )

    @property
    def current_view_group_uid(self) -> str | None:
        """UID of the innermost group in the current view stack."""
        return self.view_stack[-1] if self.view_stack else None

    def _group_path_uids(self, group_uid: str) -> list[str]:
        """Build the root-to-group UID path using parent_group_uid links."""
        if self.project_controller is None:
            return [group_uid]
        state = self.project_controller.project_state
        path: list[str] = []
        uid: str | None = group_uid
        while uid:
            group = state.get_visual_group(uid)
            if group is None:
                return [group_uid]
            path.append(uid)
            uid = group.parent_uid
        path.reverse()
        return path

    def _activate_view_stack(self) -> None:
        """Apply the current view stack to the scene."""
        if self.project_controller is None:
            return
        if self.view_stack:
            group_uid = self.view_stack[-1]
            group = self.project_controller.project_state.get_visual_group(group_uid)
            if group is None:
                self.view_stack = []
            else:
                self.project_controller.ensure_group_boundary_proxies(group)
                self.refresh_visual_groups()
                self.project_controller.apply_member_layouts(group)
                self.group_view_changed.emit()
                self.view_stack_changed.emit()
                return
        self.refresh_visual_groups()
        self.group_view_changed.emit()
        self.view_stack_changed.emit()

    def navigate_to_depth(self, depth: int) -> None:
        """Navigate to a breadcrumb depth (0 = root diagram)."""
        depth = max(0, min(depth, len(self.view_stack)))
        if depth == len(self.view_stack):
            return
        self._save_active_group_view_state()
        self.view_stack = self.view_stack[:depth]
        self._activate_view_stack()

    def navigate_out_of_group(self, group_uid: str) -> None:
        """Leave a group and its nested views in the navigation stack."""
        if group_uid not in self.view_stack:
            return
        self.navigate_to_depth(self.view_stack.index(group_uid))

    def pop_view_level(self) -> None:
        """Go up one level in the navigation stack."""
        if not self.view_stack:
            return
        self.navigate_to_depth(len(self.view_stack) - 1)

    def refresh_visual_groups(self) -> None:
        """Sync group items, member visibility, and connection display."""
        if self.project_controller is None:
            return

        state = self.project_controller.project_state
        all_member_uids: set[str] = set()
        for group in state.visual_groups:
            all_member_uids.update(
                self.project_controller._group_content_uids_for_group(group)
            )

        active_uid = self.current_view_group_uid
        active_group = state.get_visual_group(active_uid) if active_uid else None

        known_group_uids = {g.uid for g in state.visual_groups}
        for uid in list(self.group_items.keys()):
            if uid not in known_group_uids:
                item = self.group_items.pop(uid)
                self.diagram_scene.removeItem(item)

        for group in state.visual_groups:
            item = self.group_items.get(group.uid)
            if item is None:
                item = GroupItem(group, self)
                self.diagram_scene.addItem(item)
                self.group_items[group.uid] = item
            else:
                item.group = group
                if group.layout:
                    orientation = group.layout.get("orientation", "normal")
                    if orientation in {"normal", "flipped"}:
                        item.orientation = orientation
                    item.apply_geometry(
                        QPointF(
                            float(group.layout.get("x", 0.0)),
                            float(group.layout.get("y", 0.0)),
                        ),
                        QRectF(
                            0,
                            0,
                            float(group.layout.get("width", 160.0)),
                            float(group.layout.get("height", 100.0)),
                        ),
                    )
                else:
                    item.sync_boundary_ports()

        if active_group is None:
            for block_uid, block_item in self.block_items.items():
                block_item.setVisible(block_uid not in all_member_uids)
            for group_uid, group_item in self.group_items.items():
                group = state.get_visual_group(group_uid)
                group_item.setVisible(
                    group is not None and group.parent_uid is None
                )
        else:
            member_set = set(active_group.members)
            child_groups = set(active_group.child_group_uids)
            for block_uid, block_item in self.block_items.items():
                block_item.setVisible(block_uid in member_set)
            for group_uid, group_item in self.group_items.items():
                group_item.setVisible(group_uid in child_groups)

        self._refresh_group_proxies(active_group)
        self._refresh_group_port_labels()

        for conn_inst, conn_item in self.connections.items():
            src_uid = conn_inst.src_block().uid
            dst_uid = conn_inst.dst_block().uid
            visible = self._connection_visible(active_group, src_uid, dst_uid)

            conn_item.setVisible(visible)
            if visible:
                conn_item.update_position()

        self.refresh_manual_boundary_wires()

    def refresh_manual_boundary_wires(self) -> None:
        """Rebuild visual-only wires for incomplete group boundaries."""
        for wire in self.manual_boundary_wires.values():
            self.diagram_scene.removeItem(wire)
        self.manual_boundary_wires.clear()

        if self.project_controller is None:
            return

        state = self.project_controller.project_state
        active_uid = self.current_view_group_uid

        if active_uid:
            group = state.get_visual_group(active_uid)
            if group is None:
                return
            for boundary in group.boundary_ports:
                if boundary.linked_connection_uid:
                    continue
                if not boundary.linked_port_uid:
                    continue
                if not self._proxy_applies_to_active_group(group, boundary):
                    continue
                member_port = find_port(state, boundary.linked_port_uid)
                if member_port is None:
                    continue
                proxy = self.proxy_items.get(boundary.uid)
                if proxy is None:
                    continue
                child_uid = (
                    self._child_group_uid_for_block(group, member_port.block.uid)
                    if group.child_group_uids
                    else None
                )
                if child_uid is not None:
                    child_item = self.group_items.get(child_uid)
                    if child_item is None:
                        continue
                    boundary_uid = child_item.find_boundary_for_member_port(
                        member_port.block.uid,
                        member_port.name,
                    )
                    if boundary_uid is None:
                        continue
                    member_anchor = lambda item=child_item, uid=boundary_uid: item.get_boundary_anchor(uid)
                else:
                    block_item = self.get_block_item_from_instance(member_port.block)
                    if block_item is None:
                        continue
                    port_item = block_item.get_port_item(member_port.name)
                    if port_item is None:
                        continue
                    member_anchor = port_item.connection_anchor
                wire = ManualBoundaryWireItem(
                    self,
                    proxy.member_anchor,
                    member_anchor,
                    group_uid=active_uid,
                    boundary_uid=boundary.uid,
                    side="internal",
                )
                self.diagram_scene.addItem(wire)
                self.manual_boundary_wires[f"{boundary.uid}:internal"] = wire
            return

        for group in state.visual_groups:
            if group.parent_uid is not None:
                continue
            group_item = self.group_items.get(group.uid)
            if group_item is None or not group_item.isVisible():
                continue
            for boundary in group.boundary_ports:
                if boundary.linked_connection_uid:
                    continue
                if not boundary.external_port_uid:
                    continue
                external_port = find_port(state, boundary.external_port_uid)
                if external_port is None:
                    continue
                block_item = self.get_block_item_from_instance(external_port.block)
                if block_item is None or not block_item.isVisible():
                    continue
                port_item = block_item.get_port_item(external_port.name)
                if port_item is None:
                    continue
                wire = ManualBoundaryWireItem(
                    self,
                    lambda item=group_item, port=boundary: item.boundary_anchor_for(port),
                    port_item.connection_anchor,
                    group_uid=group.uid,
                    boundary_uid=boundary.uid,
                    side="external",
                )
                self.diagram_scene.addItem(wire)
                self.manual_boundary_wires[f"{boundary.uid}:external"] = wire

    def _refresh_group_port_labels(self) -> None:
        """Refresh boundary and proxy labels after connection changes."""
        for group_item in self.group_items.values():
            group_item.refresh_boundary_port_labels()
        for proxy_item in self.proxy_items.values():
            proxy_item.update()

    def _proxy_applies_to_active_group(
        self,
        group,
        boundary,
    ) -> bool:
        """Return whether a proxy belongs to the current internal group view."""
        if not boundary.linked_port_uid:
            return True
        block_uid = boundary.linked_port_uid.split(":", 1)[0]
        if block_uid in group.members:
            return True
        if group.child_group_uids:
            return self._child_group_uid_for_block(group, block_uid) is not None
        return False

    def _refresh_group_proxies(self, active_group) -> None:
        """Create or hide GroupIn/GroupOut proxy items for the active internal view."""
        if active_group is None:
            for item in self.proxy_items.values():
                item.setVisible(False)
            return

        active_boundary_uids = {
            boundary.uid
            for boundary in active_group.boundary_ports
            if self._proxy_applies_to_active_group(active_group, boundary)
        }
        for uid in list(self.proxy_items.keys()):
            if uid not in active_boundary_uids:
                item = self.proxy_items.pop(uid)
                self.diagram_scene.removeItem(item)

        for boundary in active_group.boundary_ports:
            if not self._proxy_applies_to_active_group(active_group, boundary):
                continue
            item = self.proxy_items.get(boundary.uid)
            if item is None:
                item = GroupProxyItem(boundary, self)
                self.diagram_scene.addItem(item)
                self.proxy_items[boundary.uid] = item
            else:
                item.boundary = boundary
                if boundary.proxy_layout:
                    orientation = boundary.proxy_layout.get("orientation", "normal")
                    if orientation in {"normal", "flipped"}:
                        item.orientation = orientation
                    item.setPos(
                        QPointF(
                            float(boundary.proxy_layout.get("x", 0.0)),
                            float(boundary.proxy_layout.get("y", 0.0)),
                        )
                    )
                    item._layout_port()
            item.setVisible(True)

    def _child_group_uid_for_block(self, parent_group, block_uid: str) -> str | None:
        """Return the direct child group uid that contains ``block_uid``."""
        if self.project_controller is None:
            return None
        for child_uid in parent_group.child_group_uids:
            child = self.project_controller.project_state.get_visual_group(child_uid)
            if child is None:
                continue
            if block_uid in self.project_controller._group_content_uids_for_group(child):
                return child_uid
        return None

    def _connection_visible(
        self,
        active_group,
        src_uid: str,
        dst_uid: str,
    ) -> bool:
        """Decide whether a connection should be drawn at the current view level."""
        if self.project_controller is None:
            return True

        if active_group is None:
            src_group = self.project_controller._group_exposing_boundary_for_block(
                src_uid, None
            )
            dst_group = self.project_controller._group_exposing_boundary_for_block(
                dst_uid, None
            )
            if src_group is not None and dst_group is not None:
                return src_group.uid != dst_group.uid
            return True

        members = set(active_group.members)
        src_in = src_uid in members
        dst_in = dst_uid in members

        if active_group.child_group_uids:
            content_uids = set(
                self.project_controller._group_content_uids_for_group(active_group)
            )
            src_in_content = src_uid in content_uids
            dst_in_content = dst_uid in content_uids

            if not src_in_content or not dst_in_content:
                return src_in_content != dst_in_content

            src_child = self._child_group_uid_for_block(active_group, src_uid)
            dst_child = self._child_group_uid_for_block(active_group, dst_uid)
            if src_child != dst_child:
                return True
            if src_child is None:
                return src_uid in members and dst_uid in members
            return False

        return (src_uid in members and dst_uid in members) or (src_in ^ dst_in)

    def connection_anchor_for_port_item(self, port_item: PortItem) -> QPointF:
        """Return the scene anchor for a port, redirecting through group borders when collapsed."""
        block_uid = port_item.instance.block.uid
        port_name = port_item.instance.name

        active_uid = self.current_view_group_uid
        if active_uid and self.project_controller is not None:
            group = self.project_controller.project_state.get_visual_group(active_uid)
            if group is not None:
                if group.child_group_uids:
                    child_uid = self._child_group_uid_for_block(group, block_uid)
                    if child_uid is not None:
                        child_item = self.group_items.get(child_uid)
                        if child_item is not None and child_item.isVisible():
                            boundary_uid = child_item.find_boundary_for_member_port(
                                block_uid, port_name
                            )
                            if boundary_uid is not None:
                                anchor = child_item.get_boundary_anchor(boundary_uid)
                                if anchor is not None:
                                    return anchor

                member_anchor = self._manual_proxy_anchor_for_member_port(group, port_item)
                if member_anchor is not None:
                    return member_anchor
                external_anchor = self._proxy_anchor_for_external_port(group, port_item)
                if external_anchor is not None:
                    return external_anchor
            return port_item.connection_anchor()

        for group_item in self.group_items.values():
            if not group_item.isVisible():
                continue
            exposing_group = self.project_controller._group_exposing_boundary_for_block(
                block_uid,
                self.current_view_group_uid,
            )
            if exposing_group is None or exposing_group.uid != group_item.group.uid:
                continue
            boundary_uid = group_item.find_boundary_for_member_port(block_uid, port_name)
            if boundary_uid is None:
                break
            anchor = group_item.get_boundary_anchor(boundary_uid)
            if anchor is not None:
                return anchor

        return port_item.connection_anchor()

    def proxy_item_for_port_item(self, port_item: PortItem) -> GroupProxyItem | None:
        """Return the proxy that currently owns a port's routed anchor."""
        redirected = self.connection_anchor_for_port_item(port_item)
        direct = port_item.connection_anchor()
        if (
            abs(redirected.x() - direct.x()) < 0.5
            and abs(redirected.y() - direct.y()) < 0.5
        ):
            return None
        for proxy in self.proxy_items.values():
            if not proxy.isVisible():
                continue
            anchor = proxy.member_anchor()
            if (
                abs(anchor.x() - redirected.x()) < 0.5
                and abs(anchor.y() - redirected.y()) < 0.5
            ):
                return proxy
        return None

    def routing_rect_for_port_item(self, port_item: PortItem) -> QRectF:
        """Return the obstacle rectangle used when routing wires to a port."""
        proxy = self.proxy_item_for_port_item(port_item)
        if proxy is not None:
            return proxy.mapRectToScene(proxy.rect())

        block_item = port_item.parent_block
        block_uid = port_item.instance.block.uid
        if self.project_controller is not None and self.current_view_group_uid is None:
            exposing = self.project_controller._group_exposing_boundary_for_block(
                block_uid, self.current_view_group_uid
            )
            if exposing is not None:
                group_item = self.group_items.get(exposing.uid)
                if group_item is not None and group_item.isVisible():
                    return group_item.mapRectToScene(group_item.rect())

        return block_item.mapRectToScene(block_item.rect())

    def _manual_proxy_anchor_for_member_port(self, group, port_item: PortItem) -> QPointF | None:
        """Route member ports to a proxy while the boundary is incomplete."""
        key = f"{port_item.instance.block.uid}:{port_item.instance.name}"
        for boundary in group.boundary_ports:
            if boundary.linked_connection_uid:
                continue
            if boundary.linked_port_uid != key:
                continue
            proxy = self.proxy_items.get(boundary.uid)
            if proxy is None:
                return None
            return proxy.member_anchor()
        return None

    def _proxy_anchor_for_external_port(self, group, port_item: PortItem) -> QPointF | None:
        """In internal view, attach crossing wires to the member-facing proxy port."""
        if self.project_controller is None:
            return None

        members = set(self.project_controller._group_content_uids_for_group(group))
        port_instance = port_item.instance
        for connection in self.project_controller.project_state.connections:
            if connection.src_port is not port_instance and connection.dst_port is not port_instance:
                continue

            src_uid = connection.src_block().uid
            dst_uid = connection.dst_block().uid
            src_in = src_uid in members
            dst_in = dst_uid in members
            if src_in == dst_in:
                continue

            if dst_in:
                member_uid, member_port_name = dst_uid, connection.dst_port.name
                external_port = connection.src_port
            else:
                member_uid, member_port_name = src_uid, connection.src_port.name
                external_port = connection.dst_port

            if external_port is not port_instance:
                continue

            linked_key = f"{member_uid}:{member_port_name}"
            for boundary in group.boundary_ports:
                if boundary.linked_port_uid != linked_key:
                    continue
                proxy = self.proxy_items.get(boundary.uid)
                if proxy is None:
                    return None
                return proxy.member_anchor()
        return None

    def on_proxy_moved(self, _proxy_item: GroupProxyItem) -> None:
        """Refresh wires after a group proxy is moved."""
        for conn_item in self.connections.values():
            conn_item.update_position()
        for wire in self.manual_boundary_wires.values():
            wire.update_position()

    def on_connection_route_edited(
        self,
        connection_item: ConnectionItem,
        old_points: list[QPointF] | None,
        new_points: list[QPointF] | None,
    ) -> None:
        """Record a manual wire route edit on the undo/redo stack."""
        if self.project_controller is not None:
            self.project_controller.execute_edit_connection_route(
                connection_item.instance,
                old_points,
                new_points,
            )
        connection_item.update_position()

    def enter_group(self, group_uid: str) -> None:
        """Open the internal view of a visual group."""
        if self.project_controller is None:
            return
        if self.project_controller.project_state.get_visual_group(group_uid) is None:
            return
        new_stack = self._group_path_uids(group_uid)
        if new_stack == self.view_stack:
            return
        self._save_active_group_view_state()
        self.view_stack = new_stack
        self._activate_view_stack()

    def exit_group_view(self) -> None:
        """Go up one level in the navigation stack."""
        self.pop_view_level()

    def _save_active_group_view_state(self) -> None:
        """Persist block and proxy positions for the active internal group view."""
        if self.project_controller is None or self.current_view_group_uid is None:
            return
        group = self.project_controller.project_state.get_visual_group(
            self.current_view_group_uid
        )
        if group is None:
            return
        self.project_controller.save_member_layouts(group)
        self.project_controller.save_proxy_layouts(group)

    def on_group_moved(self, group_item: GroupItem) -> None:
        """Refresh wires after a group container is moved."""
        for conn_inst, conn_item in self.connections.items():
            conn_item.update_position()
        for wire in self.manual_boundary_wires.values():
            wire.update_position()

    def get_block_item_from_instance(self, block_instance: BlockInstance) -> BlockItem | None:
        """Return the visual BlockItem for the given block instance, or None.

        Args:
            block_instance: The block model to look up.

        Returns:
            The corresponding :class:`BlockItem`, or ``None`` if not found.
        """
        return self.block_items.get(block_instance.uid)

    def create_connection_event(
        self,
        port: PortItem | GroupProxyPortItem | GroupBoundaryPortItem,
    ) -> None:
        """Begin a wire-drag interaction from the given port item."""
        if not self.pending_port:
            self.pending_port = port
            self.temp_connection = ConnectionItem(self.pending_port, None, None)
            self.diagram_scene.addItem(self.temp_connection)
            return

    def update_block_param_event(self, block_instance: BlockInstance, params: dict[str, Any]) -> None:
        """Delegate a parameter update for the given block to the project controller.

        Args:
            block_instance: The block to update.
            params: New parameter dict to apply.
        """
        self.project_controller.update_block_param(block_instance, params)

    def on_block_moved(self, block_item: BlockItem) -> None:
        """Mark the project dirty and refresh all wires connected to the moved block.

        Args:
            block_item: The block item that was repositioned.
        """
        if self.current_view_group_uid and self.project_controller is not None:
            group = self.project_controller.project_state.get_visual_group(
                self.current_view_group_uid
            )
            if (
                group is not None
                and block_item.instance.uid in group.members
            ):
                group.member_layouts[block_item.instance.uid] = (
                    self.project_controller._capture_block_layout(block_item.instance)
                )
        for conn_inst, conn_item in self.connections.items():
            if conn_inst.is_block_involved(block_item.instance):
                conn_item.update_position()
        for wire in self.manual_boundary_wires.values():
            wire.update_position()

    def on_block_ports_refreshed(self, block_item: BlockItem) -> None:
        """Refresh all wire positions after the ports of a block have been updated.

        Args:
            block_item: The block item whose ports were refreshed.
        """
        for conn_inst, conn_item in self.connections.items():
            if conn_inst.is_block_involved(block_item.instance):
                conn_item.update_position()

    def dragEnterEvent(self, event) -> None:
        """Accept drag events that carry text MIME data.

        Args:
            event: Qt drag-enter event.
        """
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dragMoveEvent(self, event) -> None:
        """Accept proposed drag-move actions unconditionally.

        Args:
            event: Qt drag-move event.
        """
        event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        """Handle a block drop by adding the corresponding block to the project.

        Args:
            event: Qt drop event carrying ``"category:block_type"`` text.
        """
        self.drop_event_pos = self.mapToScene(event.position().toPoint())
        category, block_type = event.mimeData().text().split(":")
        if category == GROUP_PORTS_CATEGORY:
            if self.current_view_group_uid is None or self.project_controller is None:
                return
            direction = "input" if block_type == GROUP_IN_TYPE else "output"
            self.project_controller.add_manual_boundary_port(
                self.current_view_group_uid,
                direction,
                self.drop_event_pos,
            )
        else:
            group_uid = self.current_view_group_uid
            if group_uid is not None and self.project_controller is not None:
                self.project_controller.add_block_in_group_view(
                    category, block_type, group_uid
                )
            else:
                self.project_controller.add_block(category, block_type)
        event.acceptProposedAction()

    def keyPressEvent(self, event) -> None:
        """Handle keyboard shortcuts for copy, paste, delete, zoom, rotate, and center.

        Args:
            event: Qt key-press event.
        """
        # UNDO / REDO
        if event.matches(QKeySequence.Undo):
            self.project_controller.undo_manager.undo()
            event.accept()
            return
        if event.matches(QKeySequence.Redo):
            self.project_controller.undo_manager.redo()
            event.accept()
            return
        if (
            event.key() == Qt.Key_Z
            and event.modifiers() == (Qt.ControlModifier | Qt.ShiftModifier)
        ):
            self.project_controller.undo_manager.redo()
            event.accept()
            return

        # COPY
        if event.key() == Qt.Key_C and event.modifiers() & Qt.ControlModifier:
            if self.project_controller.copy_selection():
                event.accept()
            return

        # PASTE
        if event.key() == Qt.Key_V and event.modifiers() & Qt.ControlModifier:
            if clipboard_has_content(self.clipboard):
                offset = 30 * (self.paste_generation + 1)
                origin = QPointF(
                    self.clipboard.anchor_x + offset,
                    self.clipboard.anchor_y + offset,
                )
                if self.project_controller.paste_clipboard_at(origin):
                    event.accept()
            return

        # DELETE
        if event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            self.delete_selected()
            return

        # ZOOM IN / OUT
        if event.key() in (Qt.Key_Plus, Qt.Key_Equal) and event.modifiers() & Qt.ControlModifier:
            self.scale_view(1.15)
            return

        if event.key() == Qt.Key_Minus and event.modifiers() & Qt.ControlModifier:
            self.scale_view(1 / 1.15)
            return

        # GROUP / UNGROUP
        if (
            event.key() == Qt.Key_G
            and event.modifiers() == (Qt.ControlModifier | Qt.ShiftModifier)
        ):
            self.project_controller.group_selected_blocks()
            event.accept()
            return
        if (
            event.key() == Qt.Key_U
            and event.modifiers() == (Qt.ControlModifier | Qt.ShiftModifier)
        ):
            self.project_controller.ungroup_selected_group()
            event.accept()
            return

        if event.key() == Qt.Key_Escape and self.view_stack:
            self.exit_group_view()
            event.accept()
            return

        # ROTATE BLOCK / GROUP / PROXY
        if event.key() == Qt.Key_R and event.modifiers() & Qt.ControlModifier:
            selected_blocks = [
                i for i in self.diagram_scene.selectedItems() if isinstance(i, BlockItem)
            ]
            selected_groups = [
                i for i in self.diagram_scene.selectedItems() if isinstance(i, GroupItem)
            ]
            selected_proxies: list[GroupProxyItem] = []
            seen_proxy_uids: set[str] = set()
            for item in self.diagram_scene.selectedItems():
                if isinstance(item, GroupProxyPortItem):
                    item = item.parent_proxy
                if not isinstance(item, GroupProxyItem):
                    continue
                if item.boundary.uid in seen_proxy_uids:
                    continue
                seen_proxy_uids.add(item.boundary.uid)
                selected_proxies.append(item)
            for item in selected_blocks:
                self.project_controller.execute_toggle_orientation(item.instance)
            for item in selected_groups:
                self.project_controller.execute_toggle_group_orientation(item.group.uid)
            if self.current_view_group_uid is not None:
                for item in selected_proxies:
                    self.project_controller.execute_toggle_proxy_orientation(
                        self.current_view_group_uid,
                        item.boundary.uid,
                    )
            if selected_blocks or selected_groups or selected_proxies:
                event.accept()
                return

        # CENTER VIEW
        if event.key() == Qt.Key_Space and not event.modifiers():
            self._center_on_diagram()
            event.accept()
            return
        super().keyPressEvent(event)

    def wheelEvent(self, event) -> None:
        """Zoom the view when Ctrl is held, otherwise scroll normally.

        Args:
            event: Qt wheel event.
        """
        if event.modifiers() & Qt.ControlModifier:
            zoom_factor = 1.15
            if event.angleDelta().y() > 0:
                self.scale_view(zoom_factor)
            else:
                self.scale_view(1 / zoom_factor)
            event.accept()
        else:
            super().wheelEvent(event)

    def mouseMoveEvent(self, event) -> None:
        """Update the temporary wire endpoint while dragging from a port.

        Args:
            event: Qt mouse-move event.
        """
        if self.temp_connection:
            pos = self.mapToScene(event.position().toPoint())
            self.temp_connection.update_temp_position(pos)
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        """Complete or cancel a wire drag on mouse release.

        Args:
            event: Qt mouse-release event.
        """
        if not self.pending_port:
            super().mouseReleaseEvent(event)
            return

        pos = self.mapToScene(event.position().toPoint())
        items = self.diagram_scene.items(pos)
        wire_types = (PortItem, GroupProxyPortItem, GroupBoundaryPortItem)
        target = next((item for item in items if isinstance(item, wire_types)), None)
        if target is None or target is self.pending_port:
            self._cancel_temp_connection()
            return

        if not (
            isinstance(self.pending_port, PortItem)
            and isinstance(target, PortItem)
        ):
            if self.project_controller.try_wire_boundary_endpoints(
                self.pending_port, target
            ):
                self._cancel_temp_connection()
                return
            self._cancel_temp_connection()
            return

        if self.project_controller.try_connect_boundary_ports(
            self.pending_port.instance,
            target.instance,
        ):
            self._cancel_temp_connection()
            return

        self.project_controller.add_connection(self.pending_port.instance, target.instance)
        self._cancel_temp_connection()

    def contextMenuEvent(self, event) -> None:
        """Show diagram context menu for grouping actions."""
        if self.project_controller is None:
            super().contextMenuEvent(event)
            return

        clicked_proxy = self._proxy_item_at(event)
        if clicked_proxy is not None:
            self._show_boundary_port_context_menu(clicked_proxy, event.globalPos())
            return

        menu = QMenu(self)
        selected_blocks = self.get_selected_block_instances()
        selected_group_uids = self.get_selected_group_uids()
        clicked_group = self._group_item_at(event)
        clicked_block = self._block_item_at(event)
        target_group_uid = (
            clicked_group.group.uid if clicked_group is not None else (
                selected_group_uids[0] if selected_group_uids else None
            )
        )

        group_action = menu.addAction("Group")
        group_action.setEnabled(len(selected_blocks) + len(selected_group_uids) >= 2)
        group_action.triggered.connect(
            lambda *_args: self.project_controller.group_selected_blocks()
        )

        if (
            self.current_view_group_uid is None
            and target_group_uid is not None
            and len(selected_blocks) == 1
        ):
            block = selected_blocks[0]
            add_to_group = menu.addAction("Add to group")
            add_to_group.setEnabled(
                self.project_controller._can_add_block_to_group(
                    target_group_uid, block.uid
                )
            )
            add_to_group.triggered.connect(
                lambda *_args, uid=target_group_uid, inst=block: (
                    self.project_controller.add_block_to_group(uid, inst)
                )
            )

        if target_group_uid is not None:
            enter_action = menu.addAction("Enter")
            enter_action.triggered.connect(
                lambda *_args, uid=target_group_uid: self.enter_group(uid)
            )
            rename_action = menu.addAction("Rename")
            rename_action.triggered.connect(
                lambda *_args, uid=target_group_uid: self._rename_group(uid)
            )
            ungroup_action = menu.addAction("Ungroup")
            ungroup_action.triggered.connect(
                lambda *_args, uid=target_group_uid: self.project_controller.ungroup(uid)
            )
        else:
            ungroup_action = menu.addAction("Ungroup")
            ungroup_action.setEnabled(False)

        if self.current_view_group_uid is not None:
            exit_action = menu.addAction("Go up")
            exit_action.triggered.connect(self.exit_group_view)
            add_in = menu.addAction("Add input")
            add_in.triggered.connect(self._add_manual_group_input)
            add_out = menu.addAction("Add output")
            add_out.triggered.connect(self._add_manual_group_output)
            if clicked_block is not None:
                remove_from_group = menu.addAction("Remove from group")
                remove_from_group.triggered.connect(
                    lambda *_args, uid=self.current_view_group_uid, block=clicked_block.instance: (
                        self.project_controller.remove_block_from_group(uid, block.uid)
                    )
                )

        menu.exec(event.globalPos())

    def delete_selected(self) -> None:
        """Remove all selected blocks and connections from the project."""
        selected_items = list(self.diagram_scene.selectedItems())
        if not selected_items:
            return
        self.project_controller.begin_macro("Delete Selection")
        try:
            removed_boundaries: set[tuple[str, str]] = set()
            for item in selected_items:
                boundary_key = self._boundary_key_for_item(item)
                if boundary_key is not None:
                    if boundary_key not in removed_boundaries:
                        removed_boundaries.add(boundary_key)
                        self.project_controller.remove_boundary_port(*boundary_key)
                    continue
                if isinstance(item, GroupItem):
                    self.project_controller.delete_group(item.group.uid)
                elif isinstance(item, BlockItem):
                    self.project_controller.remove_block(item.instance)
                elif isinstance(item, ManualBoundaryWireItem):
                    self.project_controller.disconnect_manual_boundary_side(
                        item.group_uid,
                        item.boundary_uid,
                        item.side,
                    )
                elif isinstance(item, ConnectionItem):
                    self.project_controller.remove_connection(item.instance)
        finally:
            self.project_controller.end_macro()

    def _boundary_key_for_item(self, item) -> tuple[str, str] | None:
        """Return (group_uid, boundary_uid) for a selected group boundary item."""
        if isinstance(item, GroupProxyPortItem):
            item = item.parent_proxy
        if isinstance(item, GroupProxyItem):
            if self.current_view_group_uid is None:
                return None
            return self.current_view_group_uid, item.boundary.uid
        if isinstance(item, GroupBoundaryPortItem):
            return item.parent_group.group.uid, item.boundary.uid
        return None

    def clear_scene(self) -> None:
        """Remove all blocks and connections from the scene and reset state."""
        self.diagram_scene.clear()
        self.block_items.clear()
        self.group_items.clear()
        self.proxy_items.clear()
        for wire in self.manual_boundary_wires.values():
            self.diagram_scene.removeItem(wire)
        self.manual_boundary_wires.clear()
        self.connections.clear()
        self.view_stack = []
        self.temp_connection = None
        self.pending_port = None
        self.view_stack_changed.emit()

    def scale_view(self, factor: float) -> None:
        """Scale the view by ``factor``, clamped to the allowed zoom range.

        Args:
            factor: Multiplicative zoom factor to apply.
        """
        current_scale = self.transform().m11()
        min_scale, max_scale = 0.2, 5.0

        new_scale = current_scale * factor
        if min_scale <= new_scale <= max_scale:
            self.scale(factor, factor)


    # --------------------------------------------------------------------------
    # Private Methods
    # --------------------------------------------------------------------------

    def _cancel_temp_connection(self) -> None:
        """Remove the temporary wire and reset the pending-port state."""
        self.diagram_scene.removeItem(self.temp_connection)
        self.temp_connection = None
        self.pending_port = None

    def _on_color_scheme_changed(self, *_) -> None:
        """Schedule a theme refresh after the system colour scheme changes."""
        QTimer.singleShot(0, self._apply_theme_from_system)

    def _apply_theme_from_system(self) -> None:
        """Reload the theme and repaint all scene items to match the system palette."""
        self.theme = make_theme()
        self.diagram_scene.setBackgroundBrush(self.theme.scene_bg)
        self._refresh_theme_items()
        self.viewport().update()
        self.diagram_scene.update()

    def _refresh_theme_items(self) -> None:
        """Update colours on all block and connection items to match the current theme."""
        for block in self.block_items.values():
            block.update()
            for port in block.port_items:
                port.label.setDefaultTextColor(self.theme.text)
                port.update()

        for conn in self.connections.values():
            conn.setPen(QPen(self.theme.wire, 2))
            conn.update_position()
            conn.update()

        for group in self.group_items.values():
            group.update()
            group.refresh_boundary_port_labels()
            for boundary_item in group.boundary_port_items.values():
                boundary_item.label.setDefaultTextColor(self.theme.text)

        for proxy in self.proxy_items.values():
            proxy.update()

    def _add_manual_group_input(self) -> None:
        self._add_manual_group_boundary("input")

    def _add_manual_group_output(self) -> None:
        self._add_manual_group_boundary("output")

    def _group_item_at(self, event) -> GroupItem | None:
        if hasattr(event, "position"):
            view_pos = event.position().toPoint()
        else:
            view_pos = event.pos()
        pos = self.mapToScene(view_pos)
        for item in self.diagram_scene.items(pos):
            if isinstance(item, GroupItem):
                return item
        return None

    def _block_item_at(self, event) -> BlockItem | None:
        if hasattr(event, "position"):
            view_pos = event.position().toPoint()
        else:
            view_pos = event.pos()
        pos = self.mapToScene(view_pos)
        for item in self.diagram_scene.items(pos):
            if isinstance(item, BlockItem):
                return item
        return None

    def _proxy_item_at(self, event) -> GroupProxyItem | None:
        if hasattr(event, "position"):
            view_pos = event.position().toPoint()
        else:
            view_pos = event.pos()
        pos = self.mapToScene(view_pos)
        for item in self.diagram_scene.items(pos):
            current = item
            while current is not None:
                if isinstance(current, GroupProxyItem):
                    return current
                current = current.parentItem()
        return None

    def _show_boundary_port_context_menu(
        self,
        proxy_item: GroupProxyItem,
        global_pos,
    ) -> None:
        """Show rename/reset menu for a group In/Out proxy."""
        if self.project_controller is None or self.current_view_group_uid is None:
            return

        boundary = proxy_item.boundary
        group_uid = self.current_view_group_uid
        menu = QMenu(self)
        rename_action = menu.addAction("Rename port")
        delete_action = menu.addAction("Delete port")
        reset_action = menu.addAction("Reset automatic name")
        reset_action.setEnabled(bool(boundary.label.strip()))

        action = menu.exec(global_pos)
        if action is rename_action:
            current = boundary.label if boundary.label.strip() else proxy_item.center_label()
            text, ok = QInputDialog.getText(
                self,
                "Rename Group Port",
                "Proxy label:",
                text=current,
            )
            if ok:
                self.project_controller.rename_boundary_port(
                    group_uid, boundary.uid, text
                )
        elif action is delete_action:
            self.project_controller.remove_boundary_port(group_uid, boundary.uid)
        elif action is reset_action:
            self.project_controller.rename_boundary_port(group_uid, boundary.uid, "")

    def _rename_group(self, group_uid: str) -> None:
        if self.project_controller is None:
            return
        group = self.project_controller.project_state.get_visual_group(group_uid)
        if group is None:
            return
        new_name, accepted = QInputDialog.getText(
            self,
            "Rename Group",
            "Group name:",
            text=group.name,
        )
        if accepted:
            self.project_controller.rename_visual_group(group_uid, new_name)

    def _add_manual_group_boundary(self, direction: str) -> None:
        if self.project_controller is None or self.current_view_group_uid is None:
            return
        origin = self.mapToScene(self.viewport().rect().center())
        self.project_controller.add_manual_boundary_port(
            self.current_view_group_uid,
            direction,
            origin,
        )

    def _center_on_diagram(self) -> None:
        """Fit the view to the bounding rect of all scene items with a small margin."""
        scene = self.diagram_scene
        items_rect = scene.itemsBoundingRect()

        if items_rect.isNull():
            return

        # Un peu de marge pour éviter que ça colle aux bords
        margin = 40
        items_rect.adjust(-margin, -margin, margin, margin)

        scene.setSceneRect(items_rect)
        self.fitInView(items_rect, Qt.KeepAspectRatio)
