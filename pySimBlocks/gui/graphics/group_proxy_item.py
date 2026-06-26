# ******************************************************************************
#                                  pySimBlocks
#                     Copyright (c) 2026 Université de Lille & INRIA
# ******************************************************************************

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QFont, QPainter, QPen, QPainterPath
from PySide6.QtWidgets import QGraphicsItem, QGraphicsRectItem, QStyle

from pySimBlocks.gui.models.visual_group import BoundaryPort

if TYPE_CHECKING:
    from pySimBlocks.gui.widgets.diagram_view import DiagramView


class GroupProxyPortItem(QGraphicsItem):
    """Single visible port on a GroupIn or GroupOut proxy block."""

    R = 6
    L = 15
    H = 10

    def __init__(self, is_output: bool, parent_proxy: "GroupProxyItem"):
        super().__init__(parent_proxy)
        self.is_output = is_output
        self.parent_proxy = parent_proxy

    @property
    def is_on_left_side(self) -> bool:
        return self.pos().x() < (self.parent_proxy.rect().width() * 0.5)

    def connection_anchor(self) -> QPointF:
        if self.is_output:
            x = self.L if not self.is_on_left_side else -self.L
            local = QPointF(x, 0)
        else:
            x = -self.R if self.is_on_left_side else self.R
            local = QPointF(x, 0)
        return self.mapToScene(local)

    def boundingRect(self) -> QRectF:
        return QRectF(-12, -12, 24, 24)

    def shape(self):
        path = QPainterPath()
        if self.is_output:
            tip_x = self.L if not self.is_on_left_side else -self.L
            path.moveTo(0, -self.H)
            path.lineTo(0, self.H)
            path.lineTo(tip_x, 0)
            path.closeSubpath()
        else:
            path.addEllipse(-self.R, -self.R, 2 * self.R, 2 * self.R)
        return path

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.parent_proxy.view.create_connection_event(self)
            event.accept()
            return
        super().mousePressEvent(event)

    def paint(self, painter, option, widget=None):
        t = self.parent_proxy.view.theme
        painter.setRenderHint(QPainter.Antialiasing)
        fill = t.port_out if self.is_output else t.port_in
        painter.setBrush(QBrush(fill))
        painter.setPen(QPen(t.block_border, 1))
        if self.is_output:
            path = QPainterPath()
            path.moveTo(0, -self.H)
            path.lineTo(0, self.H)
            tip_x = self.L if not self.is_on_left_side else -self.L
            path.lineTo(tip_x, 0)
            path.closeSubpath()
            painter.drawPath(path)
        else:
            painter.drawEllipse(-self.R, -self.R, 2 * self.R, 2 * self.R)


class GroupProxyItem(QGraphicsRectItem):
    """Render a GroupIn or GroupOut proxy inside a visual group.

    GroupIn exposes only an output toward group members; its external input
    lives on the parent GroupItem border. GroupOut exposes only an input from
    members; its external output lives on the parent GroupItem border.
    """

    WIDTH = 56.0
    HEIGHT = 45.0
    TYPE_LABEL_MIN_HEIGHT = 40.0
    GRID_DX = 5
    GRID_DY = 5

    def __init__(self, boundary: BoundaryPort, view: "DiagramView"):
        super().__init__(0, 0, self.WIDTH, self.HEIGHT)
        self.boundary = boundary
        self.view = view
        layout = boundary.proxy_layout or {}
        self.orientation = layout.get("orientation", "normal")
        if self.orientation not in {"normal", "flipped"}:
            self.orientation = "normal"

        if self.is_group_in:
            self.port_item = GroupProxyPortItem(is_output=True, parent_proxy=self)
        else:
            self.port_item = GroupProxyPortItem(is_output=False, parent_proxy=self)
        self._layout_port()

        self.setPos(QPointF(float(layout.get("x", 0.0)), float(layout.get("y", 0.0))))
        self.setFlag(QGraphicsRectItem.ItemIsMovable)
        self.setFlag(QGraphicsRectItem.ItemIsSelectable)
        self.setFlag(QGraphicsRectItem.ItemSendsScenePositionChanges)
        self.setZValue(0)
        self._interaction_start_pos: QPointF | None = None

    @property
    def is_group_in(self) -> bool:
        return self.boundary.direction == "input"

    @property
    def is_group_out(self) -> bool:
        return self.boundary.direction == "output"

    @property
    def kind_label(self) -> str:
        return "In" if self.is_group_in else "Out"

    def center_label(self) -> str:
        """Return proxy label from member port or manual override."""
        controller = self.view.project_controller
        if controller is None:
            return self.kind_label
        text = controller.boundary_proxy_label(self.boundary)
        return text if text else self.kind_label

    def member_anchor(self) -> QPointF:
        """Anchor used for wires between the proxy and group members."""
        return self.port_item.connection_anchor()

    def _layout_port(self) -> None:
        rect = self.rect()
        mid_y = rect.height() / 2
        flipped = self.orientation == "flipped"
        if self.is_group_in:
            self.port_item.setPos(0 if flipped else rect.width(), mid_y)
        else:
            self.port_item.setPos(rect.width() if flipped else 0, mid_y)

    def set_orientation(self, orientation: str) -> None:
        if orientation not in {"normal", "flipped"}:
            return
        self.orientation = orientation
        self._layout_port()
        layout = dict(self.boundary.proxy_layout or {})
        layout["orientation"] = orientation
        self.boundary.proxy_layout = layout
        for conn_item in self.view.connections.values():
            if conn_item.is_manual:
                conn_item.invalidate_manual_route()
        self.view.on_proxy_moved(self)
        self.update()

    def paint(self, painter, option, widget=None):
        t = self.view.theme
        selected = bool(option.state & QStyle.State_Selected)
        rect = self.rect()
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(t.block_bg_selected if selected else t.block_bg))
        painter.setPen(QPen(t.block_border_selected if selected else t.block_border, 2))
        painter.drawRect(rect)

        name_font = QFont("Sans Serif", 9)
        painter.setFont(name_font)
        painter.setPen(QPen(t.text_selected if selected else t.text))
        name_rect = QRectF(rect.x(), rect.y(), rect.width(), rect.height() * 0.60)
        painter.drawText(name_rect, int(Qt.AlignCenter | Qt.AlignBottom), self.center_label())

        if rect.height() >= self.TYPE_LABEL_MIN_HEIGHT:
            type_font = QFont("Sans Serif", 8)
            type_font.setItalic(True)
            painter.setFont(type_font)
            painter.setPen(QPen(t.text_type_selected if selected else t.text_type))
            type_rect = QRectF(
                rect.x(),
                rect.y() + rect.height() * 0.58,
                rect.width(),
                rect.height() * 0.38,
            )
            painter.drawText(type_rect, int(Qt.AlignCenter | Qt.AlignTop), self.kind_label)

    def mousePressEvent(self, event):
        self._interaction_start_pos = QPointF(self.pos())
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        start_pos = self._interaction_start_pos
        end_pos = QPointF(self.pos())
        self._interaction_start_pos = None
        super().mouseReleaseEvent(event)
        if (
            start_pos is not None
            and start_pos != end_pos
            and self.view.project_controller is not None
            and self.view.current_view_group_uid is not None
        ):
            self.view.project_controller.execute_move_proxy_layout(
                self.view.current_view_group_uid,
                self.boundary.uid,
                start_pos,
                end_pos,
            )

    def contextMenuEvent(self, event):
        if self.view is not None:
            global_pos = (
                event.screenPos()
                if hasattr(event, "screenPos")
                else event.globalPos()
            )
            self.view._show_boundary_port_context_menu(self, global_pos)
            event.accept()
            return
        super().contextMenuEvent(event)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            x = round(value.x() / self.GRID_DX) * self.GRID_DX
            y = round(value.y() / self.GRID_DY) * self.GRID_DY
            return QPointF(x, y)

        if change == QGraphicsItem.ItemPositionHasChanged and self.view.project_controller:
            pos = self.pos()
            layout = dict(self.boundary.proxy_layout or {})
            layout["x"] = float(pos.x())
            layout["y"] = float(pos.y())
            layout["orientation"] = self.orientation
            self.boundary.proxy_layout = layout
            self.view.on_proxy_moved(self)

        return super().itemChange(change, value)
