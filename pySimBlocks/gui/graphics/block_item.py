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

from typing import TYPE_CHECKING

from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QPen
from PySide6.QtWidgets import QGraphicsItem, QGraphicsRectItem, QStyle

from pySimBlocks.gui.dialogs.block_dialog import BlockDialog
from pySimBlocks.gui.graphics.port_item import PortItem

if TYPE_CHECKING:
    from pySimBlocks.gui.model.block_instance import BlockInstance
    from pySimBlocks.gui.widgets.diagram_view import DiagramView


class BlockItem(QGraphicsRectItem):
    WIDTH = 120
    HEIGHT = 60
    GRID_DX = 5
    GRID_DY = 5

    def __init__(self, 
                 instance: "BlockInstance", 
                 pos: QPointF | QPoint, 
                 view: "DiagramView",
                 layout: dict = {},
    ):
        super().__init__(0, 0, self.WIDTH, self.HEIGHT)
        self.view = view
        self.instance = instance
        self.orientation = layout.get("orientation", "normal")

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


    # --------------------------------------------------------------------------
    # Public Methods
    # --------------------------------------------------------------------------
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

        self._layout_ports()
        self.view.on_block_moved(self)
        self.update()

    # --------------------------------------------------------------------------
    # Visual Methods
    # --------------------------------------------------------------------------
    def paint(self, painter, option, widget=None):
        t = self.view.theme

        if option.state & QStyle.State_Selected:
            painter.setBrush(t.block_bg_selected)
            painter.setPen(QPen(t.block_border_selected, 3))
        else:
            painter.setBrush(t.block_bg)
            painter.setPen(QPen(t.block_border, 3))

        painter.drawRect(self.rect())
        if option.state & QStyle.State_Selected:
            painter.setPen(t.text_selected)
        else:
            painter.setPen(t.text)
        painter.drawText(self.rect(), Qt.AlignCenter, self.instance.name)

    # --------------------------------------------------------------------------
    # Event Methods
    # --------------------------------------------------------------------------
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
    def _layout_ports(self):
        inputs = [p for p in self.port_items if p.is_input]
        outputs = [p for p in self.port_items if not p.is_input]

        flipped = self.orientation == "flipped"

        if not flipped:
            self._layout_side(inputs, x=0)
            self._layout_side(outputs, x=self.WIDTH)
        else:
            self._layout_side(inputs, x=self.WIDTH)
            self._layout_side(outputs, x=0)

    # --------------------------------------------------------------
    def _layout_side(self, ports, x):
        if not ports:
            return

        step = self.HEIGHT / (len(ports) + 1)

        for i, port in enumerate(ports, start=1):
            port.setPos(x, i * step)
            port.update_label_position()
