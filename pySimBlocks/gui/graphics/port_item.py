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

from PySide6.QtWidgets import  QGraphicsEllipseItem, QGraphicsTextItem, QGraphicsItem
from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor, QPen, QFont

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pySimBlocks.gui.model.port_instance import PortInstance
    from pySimBlocks.gui.graphics.block_item import BlockItem

class PortItem(QGraphicsEllipseItem):
    R = 6

    def __init__(self, 
                instance: "PortInstance", 
                parent_block: "BlockItem",
    ):
        super().__init__(
            -self.R, -self.R, 2 * self.R, 2 * self.R, parent_block
        )

        self.instance = instance
        self.parent_block = parent_block

        self.setBrush(QBrush(QColor("white")))
        self.setPen(QPen(Qt.black, 1))
        self.setFlag(QGraphicsEllipseItem.ItemSendsScenePositionChanges)

        # -----------------------------
        # Port label (TEXT)
        # -----------------------------
        self.label = QGraphicsTextItem(self.instance.name, parent_block)
        self.label.setDefaultTextColor(Qt.black)
        self.label.setFont(QFont("Sans Serif", 8))

    def update_label_position(self):
        margin = 22
        label_rect = self.label.boundingRect()

        if self.instance.direction == "input":
            self.label.setPos(
                self.x() - label_rect.width() + margin,
                self.y() - label_rect.height() / 2,
            )
        else:
            self.label.setPos(
                self.x() - margin - self.R,
                self.y() - label_rect.height() / 2,
            )

    def mousePressEvent(self, event):
        self.parent_block.view.create_connection_event(self)
        event.accept()

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemScenePositionHasChanged:
            self.update_label_position()

        return super().itemChange(change, value)
