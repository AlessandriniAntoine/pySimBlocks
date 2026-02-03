# ******************************************************************************
#                                  pySimBlocks
#                     Copyright (c) 2026 Antoine Alessandrini
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

from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsView, QGraphicsItem, QStyle
from PySide6.QtCore import Qt, QPointF, QPoint
from PySide6.QtGui import QColor, QPen

from pySimBlocks.gui.dialogs.block_dialog import BlockDialog
from pySimBlocks.gui.graphics.port_item import PortItem
from pySimBlocks.gui.model.block_instance import BlockInstance


class BlockItem(QGraphicsRectItem):
    WIDTH = 120
    HEIGHT = 60

    def __init__(self, 
                 instance: BlockInstance, 
                 pos: QPointF | QPoint, 
                 view: QGraphicsView,
                 orientation: str = "normal"
    ):
        super().__init__(0, 0, self.WIDTH, self.HEIGHT)
        self.view = view
        self.instance = instance
        self.orientation = orientation

        self.setPos(pos)
        self.setFlag(QGraphicsRectItem.ItemIsMovable)
        self.setFlag(QGraphicsRectItem.ItemIsSelectable)
        self.setFlag(QGraphicsRectItem.ItemSendsScenePositionChanges)

        # Ports
        self.port_items: list[PortItem] = []
        self.instance.resolve_ports()
        for port in self.instance.ports:
            item = PortItem(port, self)
            self.port_items.append(item)
        self._layout_ports()


    # --------------------------------------------------------------
    def paint(self, painter, option, widget=None):
        # --- background ---
        if option.state & QStyle.State_Selected:
            painter.setBrush(QColor("#88C0D0"))
            painter.setPen(QPen(QColor("#2E3440"), 2))
        else:
            painter.setBrush(QColor("#E6F2FF"))
            painter.setPen(QPen(QColor("#4C566A"), 1))

        painter.drawRect(self.rect())

        # --- text ---
        painter.setPen(QColor("#2E3440"))
        painter.drawText(self.rect(), Qt.AlignCenter, self.instance.name)

    # --------------------------------------------------------------
    def mouseDoubleClickEvent(self, event):
        dialog = BlockDialog(self, readonly=False)
        dialog.exec()
        self.update()
        event.accept()

    # --------------------------------------------------------------
    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            for port in self.port_items:
                for c in port.connections:
                    c.update_position()
        return super().itemChange(change, value)

    # --------------------------------------------------------------
    def remove_all_connections(self):
        for port in self.port_items:
            for conn in port.connections[:]:
                conn.remove()

    # --------------------------------------------------------------
    def get_port_item(self, name:str) -> PortItem | None:
        for port in self.port_items:
            if port.instance.name == name:
                return port


    # --------------------------------------------------------------
    def refresh_ports(self):
        for item in self.port_items:
            self.scene().removeItem(item)

        self.port_items.clear()
        self.instance.resolve_ports()

        for port in self.instance.ports:
            self.port_items.append(PortItem(port, self))

        self._layout_ports()


    # --------------------------------------------------------------
    def toggle_orientation(self):
        self.orientation = "flipped" if self.orientation == "normal" else "normal"

        # reposition ports
        self._layout_ports()

        # force update connections
        for port in self.port_items:
            for c in port.connections:
                c.update_position()

        self.update()

    # --------------------------------------------------------------
    def _layout_side(self, ports, x):
        if not ports:
            return

        step = self.HEIGHT / (len(ports) + 1)

        for i, port in enumerate(ports, start=1):
            port.setPos(x, i * step)
            port.update_label_position()


    # --------------------------------------------------------------
    def _layout_ports(self):
        inputs = [p for p in self.port_items if p.instance.direction == "input"]
        outputs = [p for p in self.port_items if p.instance.direction == "output"]

        flipped = self.orientation == "flipped"

        if not flipped:
            self._layout_side(inputs, x=0)
            self._layout_side(outputs, x=self.WIDTH)
        else:
            self._layout_side(inputs, x=self.WIDTH)
            self._layout_side(outputs, x=0)
