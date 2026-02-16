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

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QGraphicsItem, QGraphicsTextItem

if TYPE_CHECKING:
    from pySimBlocks.gui.graphics.block_item import BlockItem
    from pySimBlocks.gui.model.port_instance import PortInstance


class PortItem(QGraphicsItem):
    MARGIN = 4
    R = 6   # radius input port
    L = 15  # length output port
    H = 10  # height output port
    RECT = QRectF(-8, -8, 15, 15) # bounding rect for both port types

    def __init__(self, instance: 'PortInstance', parent_block: 'BlockItem'):
        super().__init__(parent_block)

        self.instance = instance
        self.parent_block = parent_block

        self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges)
        self.setAcceptedMouseButtons(Qt.LeftButton)

        # Label
        self.t = parent_block.view.theme
        self.label = QGraphicsTextItem(self.instance.display_as, parent_block)
        self.label.setDefaultTextColor(self.t.text)
        self.label.setFont(QFont("Sans Serif", 8))

    # --------------------------------------------------------------------------
    # Properties
    # --------------------------------------------------------------------------
    @property
    def is_input(self):
        return self.instance.direction == "input"

    # --------------------------------------------------------------
    @property
    def is_on_left_side(self) -> bool:
        return self.pos().x() < (self.parent_block.rect().width() * 0.5)

    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------
    def update_label_position(self):
        label_rect = self.label.boundingRect()

        if self.is_on_left_side:
            self.label.setPos(
                self.x() + self.R + self.MARGIN,
                self.y() - label_rect.height() / 2,
            )
        else:
            self.label.setPos(
                self.x() - label_rect.width() - self.R - self.MARGIN,
                self.y() - label_rect.height() / 2,
            )

    # --------------------------------------------------------------
    def update_display_as(self):
        self.label.setPlainText(self.instance.display_as)

    # --------------------------------------------------------------
    def connection_anchor(self) -> QPointF:
        if self.is_input:
            x = -self.R if self.is_on_left_side else self.R
            local = QPointF(x, 0)
        else:
            x = self.L if not self.is_on_left_side else -self.L
            local = QPointF(x, 0)
        return self.mapToScene(local)

    # --------------------------------------------------------------
    def is_compatible(self, other: 'PortItem'):
        return self.instance.direction != other.instance.direction

    # --------------------------------------------------------------------------
    # Visuals
    # --------------------------------------------------------------------------
    def boundingRect(self) -> QRectF:
        return self.RECT

    # --------------------------------------------------------------
    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)

        fill = self.t.port_in if self.is_input else self.t.port_out

        painter.setBrush(QBrush(fill))
        painter.setPen(QPen(self.t.block_border, 1))

        if self.is_input:
            painter.drawEllipse(-self.R, -self.R, 2 * self.R, 2 * self.R)
        else:
            path = QPainterPath()
            path.moveTo(0, -self.H)
            path.lineTo(0,  self.H)
            tip_x = self.L if not self.is_on_left_side else - self.L
            path.lineTo(tip_x, 0)
            path.closeSubpath()
            painter.drawPath(path)

    # --------------------------------------------------------------
    def shape(self):
        path = QPainterPath()

        if self.is_input:
            path.addEllipse(-self.R, -self.R, 2*self.R, 2*self.R)
        else:
            tip_x = self.L if not self.is_on_left_side else -self.L
            path.moveTo(0, -self.H)
            path.lineTo(0,  self.H)
            path.lineTo(tip_x, 0)
            path.closeSubpath()

        return path

    # --------------------------------------------------------------------------
    # Event handlers
    # --------------------------------------------------------------------------
    def mousePressEvent(self, event):
        self.parent_block.view.create_connection_event(self)
        event.accept()

    # --------------------------------------------------------------
    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemScenePositionHasChanged:
            self.update_label_position()
        return super().itemChange(change, value)
