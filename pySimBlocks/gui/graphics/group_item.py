# ******************************************************************************
#                                  pySimBlocks
#                     Copyright (c) 2026 Université de Lille & INRIA
# ******************************************************************************

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QPainterPath
from PySide6.QtGui import QBrush, QFont, QPainter, QPen
from PySide6.QtWidgets import QGraphicsItem, QGraphicsRectItem, QGraphicsTextItem, QStyle

from pySimBlocks.gui.models.visual_group import BoundaryPort, VisualGroup

if TYPE_CHECKING:
    from pySimBlocks.gui.widgets.diagram_view import DiagramView


class GroupBoundaryPortItem(QGraphicsItem):
    """Visual port on a group rectangle border."""

    R = 6
    L = 15
    H = 10

    MARGIN = 4

    def __init__(self, boundary: BoundaryPort, parent_group: "GroupItem"):
        super().__init__(parent_group)
        self.boundary = boundary
        self.parent_group = parent_group
        self.setAcceptedMouseButtons(Qt.LeftButton)
        t = parent_group.view.theme
        self.label = QGraphicsTextItem(self)
        self.label.setDefaultTextColor(t.text)
        self.label.setFont(QFont("Sans Serif", 8))
        self.update_port_label()

    @property
    def is_input(self) -> bool:
        return self.boundary.direction == "input"

    @property
    def is_on_left_side(self) -> bool:
        return self.pos().x() < (self.parent_group.rect().width() * 0.5)

    def connection_anchor(self) -> QPointF:
        if self.is_input:
            x = -self.R if self.is_on_left_side else self.R
            local = QPointF(x, 0)
        else:
            x = self.L if not self.is_on_left_side else -self.L
            local = QPointF(x, 0)
        return self.mapToScene(local)

    def update_port_label(self) -> None:
        """Refresh the external port label shown next to the boundary port."""
        controller = self.parent_group.view.project_controller
        text = ""
        if controller is not None:
            text = controller.boundary_port_flow_label(
                self.parent_group.group,
                self.boundary,
            )
        self.label.setPlainText(text)
        self.label.setVisible(bool(text))
        self._layout_port_label()

    def _layout_port_label(self) -> None:
        label_rect = self.label.boundingRect()
        if self.is_on_left_side:
            self.label.setPos(
                self.R + self.MARGIN,
                -label_rect.height() / 2,
            )
        else:
            self.label.setPos(
                -label_rect.width() - self.R - self.MARGIN,
                -label_rect.height() / 2,
            )

    def boundingRect(self) -> QRectF:
        return QRectF(-10, -10, 20, 20)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemScenePositionHasChanged:
            self._layout_port_label()
        return super().itemChange(change, value)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.parent_group.view.create_connection_event(self)
            event.accept()
            return
        super().mousePressEvent(event)

    def shape(self):
        path = QPainterPath()
        if self.is_input:
            path.addEllipse(-self.R, -self.R, 2 * self.R, 2 * self.R)
        else:
            tip_x = self.L if not self.is_on_left_side else -self.L
            path.moveTo(0, -self.H)
            path.lineTo(0, self.H)
            path.lineTo(tip_x, 0)
            path.closeSubpath()
        return path

    def paint(self, painter, option, widget=None):
        t = self.parent_group.view.theme
        painter.setRenderHint(QPainter.Antialiasing)
        fill = t.port_in if self.is_input else t.port_out
        painter.setBrush(QBrush(fill))
        painter.setPen(QPen(t.block_border, 1))
        if self.is_input:
            painter.drawEllipse(-self.R, -self.R, 2 * self.R, 2 * self.R)
        else:
            from PySide6.QtGui import QPainterPath

            path = QPainterPath()
            path.moveTo(0, -self.H)
            path.lineTo(0, self.H)
            tip_x = self.L if not self.is_on_left_side else -self.L
            path.lineTo(tip_x, 0)
            path.closeSubpath()
            painter.drawPath(path)


class GroupItem(QGraphicsRectItem):
    """Render a visual group container on the diagram."""

    MIN_WIDTH = 80.0
    MIN_HEIGHT = 50.0
    GRID_DX = 5
    GRID_DY = 5
    SELECTION_HANDLE_SIZE = 8
    SELECTION_HANDLE_HIT_SIZE = 16

    def __init__(self, group: VisualGroup, view: "DiagramView"):
        layout = group.layout or {}
        width = max(float(layout.get("width", 160.0)), self.MIN_WIDTH)
        height = max(float(layout.get("height", 100.0)), self.MIN_HEIGHT)
        super().__init__(0, 0, width, height)
        self.group = group
        self.view = view
        self.orientation = layout.get("orientation", "normal")
        if self.orientation not in {"normal", "flipped"}:
            self.orientation = "normal"
        self.boundary_port_items: dict[str, GroupBoundaryPortItem] = {}
        self._resize_handle: str | None = None
        self._resize_start_mouse: QPointF | None = None
        self._resize_start_pos: QPointF | None = None
        self._resize_start_width = width
        self._resize_start_height = height
        self._interaction_start_pos: QPointF | None = None
        self._interaction_start_rect: QRectF | None = None
        self._syncing_geometry = False

        x = float(layout.get("x", 0.0))
        y = float(layout.get("y", 0.0))
        self.setPos(QPointF(x, y))
        self.setFlag(QGraphicsRectItem.ItemIsMovable)
        self.setFlag(QGraphicsRectItem.ItemIsSelectable)
        self.setFlag(QGraphicsRectItem.ItemSendsScenePositionChanges)
        self.setZValue(-1)
        self.sync_boundary_ports()

    def _border_boundary_ports(self) -> list[BoundaryPort]:
        """Return boundary ports that should appear on the group rectangle."""
        return list(self.group.boundary_ports)

    def boundary_anchor_for(self, boundary: BoundaryPort) -> QPointF:
        """Return the scene anchor for a boundary port on this group."""
        port_item = self.boundary_port_items.get(boundary.uid)
        if port_item is not None:
            return port_item.connection_anchor()
        return self._boundary_anchor_from_geometry(boundary)

    def _boundaries_for_direction(self, direction: str) -> list[BoundaryPort]:
        """Return border ports for one side in stable display order."""
        previous_y = {
            uid: float(item.pos().y())
            for uid, item in self.boundary_port_items.items()
        }
        return sorted(
            [
                port
                for port in self._border_boundary_ports()
                if port.direction == direction
            ],
            key=lambda boundary: self._border_sort_key(boundary, previous_y),
        )

    def _boundary_anchor_from_geometry(self, boundary: BoundaryPort) -> QPointF:
        """Compute a boundary anchor when no border port item is shown."""
        rect = self.rect()
        same_direction = self._boundaries_for_direction(boundary.direction)
        if boundary not in same_direction:
            same_direction = [
                port
                for port in self.group.boundary_ports
                if port.direction == boundary.direction
            ]
        index = same_direction.index(boundary) if boundary in same_direction else 0
        total = len(same_direction)
        y = rect.height() * (index + 1) / (total + 1)
        flipped = self.orientation == "flipped"
        if boundary.direction == "input":
            local = (
                QPointF(rect.width() + GroupBoundaryPortItem.R, y)
                if flipped
                else QPointF(-GroupBoundaryPortItem.R, y)
            )
        else:
            local = (
                QPointF(-GroupBoundaryPortItem.L, y)
                if flipped
                else QPointF(rect.width() + GroupBoundaryPortItem.L, y)
            )
        return self.mapToScene(local)

    def _border_sort_key(
        self,
        boundary: BoundaryPort,
        previous_y: dict[str, float],
    ) -> tuple[float, str]:
        """Keep border ports in a stable vertical order across rebuilds."""
        if boundary.uid in previous_y:
            return (previous_y[boundary.uid], boundary.uid)
        if boundary.proxy_layout:
            return (float(boundary.proxy_layout.get("y", 0.0)), boundary.uid)
        return (1e9, boundary.linked_port_uid or boundary.uid)

    def sync_boundary_ports(self) -> None:
        """Rebuild boundary port items from group metadata."""
        previous_y = {
            uid: float(item.pos().y())
            for uid, item in self.boundary_port_items.items()
        }
        for item in list(self.boundary_port_items.values()):
            item.setParentItem(None)
        self.boundary_port_items.clear()

        border_ports = self._border_boundary_ports()
        inputs = sorted(
            [p for p in border_ports if p.direction == "input"],
            key=lambda boundary: self._border_sort_key(boundary, previous_y),
        )
        outputs = sorted(
            [p for p in border_ports if p.direction == "output"],
            key=lambda boundary: self._border_sort_key(boundary, previous_y),
        )
        rect = self.rect()
        flipped = self.orientation == "flipped"
        width = rect.width()

        for index, boundary in enumerate(inputs):
            item = GroupBoundaryPortItem(boundary, self)
            y = rect.height() * (index + 1) / (len(inputs) + 1)
            item.setPos(width if flipped else 0, y)
            item.update_port_label()
            self.boundary_port_items[boundary.uid] = item

        for index, boundary in enumerate(outputs):
            item = GroupBoundaryPortItem(boundary, self)
            y = rect.height() * (index + 1) / (len(outputs) + 1)
            item.setPos(0 if flipped else width, y)
            item.update_port_label()
            self.boundary_port_items[boundary.uid] = item

    def set_orientation(self, orientation: str) -> None:
        if orientation not in {"normal", "flipped"}:
            return
        self.orientation = orientation
        self.sync_boundary_ports()
        layout = dict(self.group.layout or {})
        layout["orientation"] = orientation
        self.group.layout = layout
        members = set(
            self.view.project_controller._group_content_uids_for_group(self.group)
        )
        for conn_inst, conn_item in self.view.connections.items():
            if (
                conn_inst.src_block().uid in members
                or conn_inst.dst_block().uid in members
            ) and conn_item.is_manual:
                conn_item.invalidate_manual_route()
        self.view.on_group_moved(self)
        self.update()

    def refresh_boundary_port_labels(self) -> None:
        """Update external port labels after diagram connections change."""
        for item in self.boundary_port_items.values():
            item.update_port_label()

    def get_boundary_anchor(self, boundary_uid: str) -> QPointF | None:
        boundary = next(
            (port for port in self.group.boundary_ports if port.uid == boundary_uid),
            None,
        )
        if boundary is None:
            return None
        return self.boundary_anchor_for(boundary)

    def find_boundary_for_member_port(self, block_uid: str, port_name: str) -> str | None:
        key = f"{block_uid}:{port_name}"
        for boundary in self.group.boundary_ports:
            if boundary.linked_port_uid == key:
                return boundary.uid
        return None

    def paint(self, painter, option, widget=None):
        t = self.view.theme
        selected = bool(option.state & QStyle.State_Selected)
        painter.setRenderHint(QPainter.Antialiasing)

        if selected:
            painter.setBrush(QBrush(t.block_bg_selected))
            painter.setPen(QPen(t.block_border_selected, 3))
        else:
            painter.setBrush(QBrush(t.block_bg))
            painter.setPen(QPen(t.block_border, 2, Qt.DashLine))

        painter.drawRect(self.rect())

        painter.setPen(QPen(t.text_selected if selected else t.text))
        painter.setFont(QFont("Sans Serif", 9, QFont.Bold))
        painter.drawText(
            self.rect().adjusted(4, 4, -4, -4),
            int(Qt.AlignTop | Qt.AlignHCenter),
            self.group.name,
        )

        if selected:
            half = self.SELECTION_HANDLE_SIZE / 2
            r = self.rect()
            corners = [
                (r.left(), r.top()),
                (r.right(), r.top()),
                (r.left(), r.bottom()),
                (r.right(), r.bottom()),
            ]
            painter.setPen(QPen(t.block_border_selected, 1))
            painter.setBrush(t.text_selected)
            for x, y in corners:
                painter.drawRect(
                    x - half, y - half, self.SELECTION_HANDLE_SIZE, self.SELECTION_HANDLE_SIZE
                )

    def mousePressEvent(self, event):
        self._interaction_start_pos = QPointF(self.pos())
        self._interaction_start_rect = QRectF(self.rect())
        if self.isSelected():
            handle = self._handle_at(event.pos())
            if handle is not None:
                self._resize_handle = handle
                self._resize_start_mouse = event.scenePos()
                self._resize_start_pos = self.pos()
                self._resize_start_width = self.rect().width()
                self._resize_start_height = self.rect().height()
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._resize_handle and self._resize_start_mouse and self._resize_start_pos:
            delta = event.scenePos() - self._resize_start_mouse
            dx = round(delta.x() / self.GRID_DX) * self.GRID_DX
            dy = round(delta.y() / self.GRID_DY) * self.GRID_DY

            start_x = self._resize_start_pos.x()
            start_y = self._resize_start_pos.y()
            start_w = self._resize_start_width
            start_h = self._resize_start_height

            if self._resize_handle in ("tl", "bl"):
                new_x = min(start_x + dx, start_x + start_w - self.MIN_WIDTH)
                new_w = max(self.MIN_WIDTH, (start_x + start_w) - new_x)
            else:
                new_x = start_x
                new_w = max(self.MIN_WIDTH, start_w + dx)

            if self._resize_handle in ("tl", "tr"):
                new_y = min(start_y + dy, start_y + start_h - self.MIN_HEIGHT)
                new_h = max(self.MIN_HEIGHT, (start_y + start_h) - new_y)
            else:
                new_y = start_y
                new_h = max(self.MIN_HEIGHT, start_h + dy)

            self.setPos(QPointF(new_x, new_y))
            self.setRect(0, 0, new_w, new_h)
            self.sync_boundary_ports()
            self.view.on_group_moved(self)
            self.update()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        start_pos = self._interaction_start_pos
        start_rect = self._interaction_start_rect
        end_pos = QPointF(self.pos())
        end_rect = QRectF(self.rect())

        self._resize_handle = None
        self._resize_start_mouse = None
        self._resize_start_pos = None
        self._interaction_start_pos = None
        self._interaction_start_rect = None
        super().mouseReleaseEvent(event)

        if start_pos is None or start_rect is None:
            return
        if start_pos != end_pos or start_rect != end_rect:
            if self.view.project_controller:
                self.view.project_controller.execute_move_resize_group(
                    self.group.uid,
                    start_pos,
                    start_rect,
                    end_pos,
                    end_rect,
                )

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            if self._syncing_geometry:
                return value
            x = round(value.x() / self.GRID_DX) * self.GRID_DX
            y = round(value.y() / self.GRID_DY) * self.GRID_DY
            return QPointF(x, y)

        if (
            change == QGraphicsItem.ItemPositionHasChanged
            and not self._syncing_geometry
            and self._resize_handle is None
        ):
            self.view.on_group_moved(self)

        return super().itemChange(change, value)

    def apply_geometry(self, pos: QPointF, rect: QRectF) -> None:
        """Apply position and size without triggering layout side effects."""
        self._syncing_geometry = True
        try:
            self.setRect(0, 0, rect.width(), rect.height())
            self.setPos(QPointF(pos))
            self.sync_boundary_ports()
        finally:
            self._syncing_geometry = False
        self.group.layout = {
            "x": float(pos.x()),
            "y": float(pos.y()),
            "width": float(rect.width()),
            "height": float(rect.height()),
            "orientation": self.orientation,
        }

    def mouseDoubleClickEvent(self, event):
        self.view.enter_group(self.group.uid)
        event.accept()

    def _handle_hit_rects(self) -> dict[str, QRectF]:
        half = self.SELECTION_HANDLE_HIT_SIZE / 2
        r = self.rect()
        return {
            "tl": QRectF(
                r.left() - half, r.top() - half,
                self.SELECTION_HANDLE_HIT_SIZE, self.SELECTION_HANDLE_HIT_SIZE,
            ),
            "tr": QRectF(
                r.right() - half, r.top() - half,
                self.SELECTION_HANDLE_HIT_SIZE, self.SELECTION_HANDLE_HIT_SIZE,
            ),
            "bl": QRectF(
                r.left() - half, r.bottom() - half,
                self.SELECTION_HANDLE_HIT_SIZE, self.SELECTION_HANDLE_HIT_SIZE,
            ),
            "br": QRectF(
                r.right() - half, r.bottom() - half,
                self.SELECTION_HANDLE_HIT_SIZE, self.SELECTION_HANDLE_HIT_SIZE,
            ),
        }

    def _handle_at(self, local_pos: QPointF) -> str | None:
        for name, rect in self._handle_hit_rects().items():
            if rect.contains(local_pos):
                return name
        return None
