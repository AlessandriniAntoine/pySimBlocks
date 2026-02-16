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

from typing import TYPE_CHECKING

from PySide6.QtCore import QPoint, QPointF, QRectF, Qt
from PySide6.QtGui import QPainterPath, QPen
from PySide6.QtWidgets import QGraphicsItem, QGraphicsRectItem, QStyle

from pySimBlocks.gui.dialogs.block_dialog import BlockDialog
from pySimBlocks.gui.graphics.port_item import PortItem

if TYPE_CHECKING:
    from pySimBlocks.gui.model.block_instance import BlockInstance
    from pySimBlocks.gui.widgets.diagram_view import DiagramView


class BlockItem(QGraphicsRectItem):
    WIDTH = 120
    HEIGHT = 60
    MIN_WIDTH = 40
    MIN_HEIGHT = 30
    GRID_DX = 5
    GRID_DY = 5
    SELECTION_HANDLE_SIZE = 8
    SELECTION_HANDLE_HIT_SIZE = 16

    def __init__(self,
                 instance: "BlockInstance",
                 pos: QPointF | QPoint,
                 view: "DiagramView",
                 layout: dict | None = None,
    ):
        layout = layout or {}
        width = layout.get("width", self.WIDTH)
        height = layout.get("height", self.HEIGHT)
        width = float(width) if isinstance(width, (int, float)) else float(self.WIDTH)
        height = float(height) if isinstance(height, (int, float)) else float(self.HEIGHT)
        width = max(float(self.MIN_WIDTH), width)
        height = max(float(self.MIN_HEIGHT), height)
        super().__init__(0, 0, width, height)
        self.view = view
        self.instance = instance
        self.orientation = layout.get("orientation", "normal")
        self._resize_handle: str | None = None
        self._resize_start_mouse: QPointF | None = None
        self._resize_start_pos: QPointF | None = None
        self._resize_start_width = self.WIDTH
        self._resize_start_height = self.HEIGHT

        self.setPos(pos)
        self.setFlag(QGraphicsRectItem.ItemIsMovable)
        self.setFlag(QGraphicsRectItem.ItemIsSelectable)
        self.setFlag(QGraphicsRectItem.ItemSendsScenePositionChanges)

        # Ports
        self.port_items: list[PortItem] = []
        for port in self.instance.ports:
            item = PortItem(port, self)
            self.port_items.append(item)
        self._layout_ports()


    # --------------------------------------------------------------------------
    # Public Methods
    # --------------------------------------------------------------------------
    def get_port_item(self, name:str) -> PortItem | None:
        for port in self.port_items:
            if port.instance.name == name:
                return port

    # --------------------------------------------------------------
    def refresh_ports(self):

        for item in list(self.port_items):
            if item.instance not in self.instance.ports:
                self.scene().removeItem(item)
                self.port_items.remove(item)

        displayed_ports = {item.instance for item in self.port_items}

        for port in self.instance.ports:
            if port not in displayed_ports:
                item = PortItem(port, self)
                self.port_items.append(item)
        
        self._layout_ports()
        for item in self.port_items:
            item.update_display_as()
        self.view.on_block_moved(self)

    # --------------------------------------------------------------
    def toggle_orientation(self):
        self.orientation = "flipped" if self.orientation == "normal" else "normal"

        self._layout_ports()
        self.view.on_block_moved(self)
        self.update()

    # --------------------------------------------------------------------------
    # Visual Methods
    # --------------------------------------------------------------------------
    def boundingRect(self) -> QRectF:
        half = self.SELECTION_HANDLE_HIT_SIZE / 2
        return self.rect().adjusted(-half, -half, half, half)

    # --------------------------------------------------------------
    def shape(self) -> QPainterPath:
        path = QPainterPath()
        path.addRect(self.rect())
        for rect in self._handle_hit_rects().values():
            path.addRect(rect)
        return path

    # --------------------------------------------------------------
    def paint(self, painter, option, widget=None):
        t = self.view.theme
        selected = bool(option.state & QStyle.State_Selected)

        if selected:
            painter.setBrush(t.block_bg_selected)
            painter.setPen(QPen(t.block_border_selected, 3))
        else:
            painter.setBrush(t.block_bg)
            painter.setPen(QPen(t.block_border, 3))

        painter.drawRect(self.rect())
        if selected:
            painter.setPen(t.text_selected)
        else:
            painter.setPen(t.text)
        painter.drawText(self.rect(), Qt.AlignCenter, self.instance.name)

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
                painter.drawRect(x - half, y - half, self.SELECTION_HANDLE_SIZE, self.SELECTION_HANDLE_SIZE)

    # --------------------------------------------------------------------------
    # Event Methods
    # --------------------------------------------------------------------------
    def mousePressEvent(self, event):
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

    # --------------------------------------------------------------
    def mouseMoveEvent(self, event):
        if self._resize_handle and self._resize_start_mouse and self._resize_start_pos:
            delta = event.scenePos() - self._resize_start_mouse
            dx = round(delta.x() / self.GRID_DX) * self.GRID_DX
            dy = round(delta.y() / self.GRID_DY) * self.GRID_DY

            start_x = self._resize_start_pos.x()
            start_y = self._resize_start_pos.y()
            start_w = self._resize_start_width
            start_h = self._resize_start_height

            if self._resize_handle in ("tl", "bl"):  # drag left edge
                new_x = min(start_x + dx, start_x + start_w - self.MIN_WIDTH)
                new_w = max(self.MIN_WIDTH, (start_x + start_w) - new_x)
            else:  # drag right edge
                new_x = start_x
                new_w = max(self.MIN_WIDTH, start_w + dx)

            if self._resize_handle in ("tl", "tr"):  # drag top edge
                new_y = min(start_y + dy, start_y + start_h - self.MIN_HEIGHT)
                new_h = max(self.MIN_HEIGHT, (start_y + start_h) - new_y)
            else:  # drag bottom edge
                new_y = start_y
                new_h = max(self.MIN_HEIGHT, start_h + dy)

            self.setPos(QPointF(new_x, new_y))
            self.setRect(0, 0, new_w, new_h)
            self._layout_ports()
            self.view.on_block_moved(self)
            self.update()
            event.accept()
            return

        super().mouseMoveEvent(event)

    # --------------------------------------------------------------
    def mouseReleaseEvent(self, event):
        self._resize_handle = None
        self._resize_start_mouse = None
        self._resize_start_pos = None
        super().mouseReleaseEvent(event)

    # --------------------------------------------------------------
    def mouseDoubleClickEvent(self, event):
        dialog = BlockDialog(self, readonly=False)
        dialog.exec()
        self.update()
        event.accept()

    # --------------------------------------------------------------
    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            x = round(value.x() / self.GRID_DX) * self.GRID_DX
            y = round(value.y() / self.GRID_DY) * self.GRID_DY
            return QPointF(x, y)

        if change == QGraphicsItem.ItemPositionHasChanged:
            self.view.on_block_moved(self)

        return super().itemChange(change, value)

    # --------------------------------------------------------------------------
    # Private Methods
    # --------------------------------------------------------------------------
    def _handle_hit_rects(self) -> dict[str, QRectF]:
        half = self.SELECTION_HANDLE_HIT_SIZE / 2
        r = self.rect()
        return {
            "tl": QRectF(r.left() - half, r.top() - half, self.SELECTION_HANDLE_HIT_SIZE, self.SELECTION_HANDLE_HIT_SIZE),
            "tr": QRectF(r.right() - half, r.top() - half, self.SELECTION_HANDLE_HIT_SIZE, self.SELECTION_HANDLE_HIT_SIZE),
            "bl": QRectF(r.left() - half, r.bottom() - half, self.SELECTION_HANDLE_HIT_SIZE, self.SELECTION_HANDLE_HIT_SIZE),
            "br": QRectF(r.right() - half, r.bottom() - half, self.SELECTION_HANDLE_HIT_SIZE, self.SELECTION_HANDLE_HIT_SIZE),
        }

    # --------------------------------------------------------------
    def _handle_at(self, local_pos: QPointF) -> str | None:
        for name, rect in self._handle_hit_rects().items():
            if rect.contains(local_pos):
                return name
        return None

    # --------------------------------------------------------------
    def _layout_ports(self):
        inputs = [p for p in self.port_items if p.is_input]
        outputs = [p for p in self.port_items if not p.is_input]

        flipped = self.orientation == "flipped"
        width = self.rect().width()

        if not flipped:
            self._layout_side(inputs, x=0)
            self._layout_side(outputs, x=width)
        else:
            self._layout_side(inputs, x=width)
            self._layout_side(outputs, x=0)

    # --------------------------------------------------------------
    def _layout_side(self, ports, x):
        if not ports:
            return

        step = self.rect().height() / (len(ports) + 1)

        for i, port in enumerate(ports, start=1):
            port.setPos(x, i * step)
            port.update_label_position()
