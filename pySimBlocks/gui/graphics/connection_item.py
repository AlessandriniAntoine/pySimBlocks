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

from PySide6.QtWidgets import QGraphicsItem, QGraphicsPathItem
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPen, QPainterPath, QPainterPathStroker

from pySimBlocks.gui.model.connection_instance import ConnectionInstance

class ConnectionItem(QGraphicsPathItem):
    def __init__(self, 
                 port1, # PortItem, circular import
                 port2, # PortItem, circular import
                 instance: ConnectionInstance):
        super().__init__()
        self.setFlag(QGraphicsItem.ItemIsSelectable)

        self.port1 = port1
        self.port2 = port2
        self.instance = instance
        self.setPen(QPen(Qt.black, 2))
        self.update_position()
        self.setZValue(1)  # les connexions passent sous les blocs

    # --------------------------------------------------------------
    def update_position(self):
        p1 = self.port1.connection_anchor()
        p2 = self.port2.connection_anchor()

        offset = 25
        margin = 20

        src_block = self.port1.parent_block
        dst_block = self.port2.parent_block

        src_rect = src_block.sceneBoundingRect()
        dst_rect = dst_block.sceneBoundingRect()

        path = QPainterPath(p1)

        # -------------------------------------------------
        # CAS FORWARD (gauche → droite)
        # -------------------------------------------------
        if p2.x() > p1.x():
            mid_x = (p1.x() + p2.x()) * 0.5
            path.lineTo(mid_x, p1.y())
            path.lineTo(mid_x, p2.y())
            path.lineTo(p2)

        # -------------------------------------------------
        # CAS FEEDBACK (retour)
        # -------------------------------------------------
        else:
            src_rect = self.port1.parent_block.sceneBoundingRect()
            dst_rect = self.port2.parent_block.sceneBoundingRect()

            candidates = []

            # --- au-dessus ---
            y_above = min(src_rect.top(), dst_rect.top()) - margin
            candidates.append(y_above)

            # --- en dessous ---
            y_below = max(src_rect.bottom(), dst_rect.bottom()) + margin
            candidates.append(y_below)

            # --- entre les deux (si possible) ---
            if src_rect.bottom() < dst_rect.top():
                candidates.append((src_rect.bottom() + dst_rect.top()) / 2)
            elif dst_rect.bottom() < src_rect.top():
                candidates.append((dst_rect.bottom() + src_rect.top()) / 2)

            # choisir le plus court
            route_y = min(
                candidates,
                key=lambda y: abs(p1.y() - y) + abs(p2.y() - y)
            )

            path.lineTo(p1.x() + offset, p1.y())
            path.lineTo(p1.x() + offset, route_y)
            path.lineTo(p2.x() - offset, route_y)
            path.lineTo(p2.x() - offset, p2.y())
            path.lineTo(p2)

        self.setPath(path)


    # --------------------------------------------------------------
    def remove(self):
        if self in self.port1.connections:
            self.port1.connections.remove(self)
        if self in self.port2.connections:
            self.port2.connections.remove(self)

    # --------------------------------------------------------------
    def shape(self):
        """
        Zone cliquable = uniquement autour du câble,
        pas toute la bounding box.
        """
        stroker = QPainterPathStroker()
        stroker.setWidth(6)  # zone cliquable (px)

        return stroker.createStroke(self.path())
