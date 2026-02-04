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

from PySide6.QtCore import QRectF, Qt, QPointF
from PySide6.QtGui import QBrush, QColor, QFont, QPainterPath, QPen, QPainter
from PySide6.QtWidgets import QGraphicsItem, QGraphicsTextItem

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pySimBlocks.gui.model.port_instance import PortInstance
    from pySimBlocks.gui.graphics.block_item import BlockItem


class PortItem(QGraphicsItem):
    R = 6
    INPUT_COLOR = QColor("#4A90E2")
    OUTPUT_COLOR = QColor("#E67E22")

    def __init__(self, instance: 'PortInstance', parent_block: 'BlockItem'):
        super().__init__(parent_block)

        self.instance = instance
        self.parent_block = parent_block

        self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges)
        self.setAcceptedMouseButtons(Qt.LeftButton)

        # Label
        self.label = QGraphicsTextItem(self.instance.name, parent_block)
        self.label.setDefaultTextColor(Qt.black)
        self.label.setFont(QFont("Sans Serif", 8))


    # --------------------------------------------------------------------------
    # Visuals 
    # --------------------------------------------------------------------------
    def boundingRect(self) -> QRectF:
        return QRectF(
            -self.R - 1,
            -self.R - 1,
            2 * self.R + 2,
            2 * self.R + 2,
        )

    # --------------------------------------------------------------
    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)

        color = (
            self.INPUT_COLOR
            if self.instance.direction == "input"
            else self.OUTPUT_COLOR
        )

        painter.setBrush(QBrush(color))
        painter.setPen(QPen(Qt.black, 1))

        if self.instance.direction == "input":
            # ● Cercle
            painter.drawEllipse(-self.R, -self.R, 2 * self.R, 2 * self.R)

        else:
            # ▶ Triangle (sortie)
            path = QPainterPath()
            path.moveTo(0, -self.R)
            path.lineTo(0,  self.R)
            path.lineTo(2*self.R,  0)
            path.closeSubpath()
            painter.drawPath(path)

    # --------------------------------------------------------------
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

    def connection_anchor(self) -> QPointF:
        """
        Point exact (en coordonnées scène) où une connexion doit s'accrocher.
        """
        if self.is_input:
            local = QPointF(-self.R, 0)
        else:
            local = QPointF(2*self.R, 0)
        return self.mapToScene(local)


    # --------------------------------------------------------------------------
    # Interaction
    # --------------------------------------------------------------------------
    def mousePressEvent(self, event):
        self.parent_block.view.create_connection_event(self)
        event.accept()

    @property
    def is_input(self):
        return self.instance.direction == "input"

    # --------------------------------------------------------------
    def shape(self):
        path = QPainterPath()

        if self.is_input:
            # Cercle centré
            path.addEllipse(-self.R, -self.R, 2*self.R, 2*self.R)

        else:
            # Triangle de sortie (même géométrie que paint)
            path.moveTo(0, -self.R)
            path.lineTo(0,  self.R)
            path.lineTo(2*self.R, 0)
            path.closeSubpath()

        return path

    # --------------------------------------------------------------
    def is_compatible(self, other: 'PortItem'):
        return self.instance.direction != other.instance.direction

    # --------------------------------------------------------------
    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemScenePositionHasChanged:
            self.update_label_position()

        return super().itemChange(change, value)
