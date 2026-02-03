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

        t = self.port1.parent_block.view.theme
        self.setPen(QPen(t.wire, 3))
        self.setZValue(1)

        self.update_position()

    # --------------------------------------------------------------
    def update_position(self):
        p1 = self.port1.connection_anchor()
        p2 = self.port2.connection_anchor()

        offset = 8
        margin = 12
        detour = 8

        src_block = self.port1.parent_block
        dst_block = self.port2.parent_block
        src_rect = src_block.sceneBoundingRect()
        dst_rect = dst_block.sceneBoundingRect()

        # sign: outward direction from source and into destination (depends on side)
        src_out_sign = 1 if not self.port1.is_on_left_side else -1
        dst_in_sign = -1 if self.port2.is_on_left_side else 1

        p1_out = QPointF(p1.x() + src_out_sign * offset, p1.y())
        p2_in  = QPointF(p2.x() + dst_in_sign  * offset, p2.y())

        path = QPainterPath(p1)

        # -------------------------------------------------
        # Decide if this must be treated as feedback (U-turn)
        # -------------------------------------------------
        same_block = (src_block is dst_block)

        # if destination is "behind" the outward direction => U-turn
        u_turn = ((p2_in.x() - p1_out.x()) * src_out_sign) < 0

        is_feedback = same_block or u_turn

        # -------------------------------------------------
        # FORWARD (no U-turn)
        # -------------------------------------------------
        if not is_feedback:
            # Path "standard" en 3 segments
            mid_x = (p1_out.x() + p2_in.x()) * 0.5
            candidate = QPainterPath(p1)
            candidate.lineTo(p1_out)
            candidate.lineTo(mid_x, p1.y())
            candidate.lineTo(mid_x, p2.y())
            candidate.lineTo(p2_in)
            candidate.lineTo(p2)

            # Check collision avec src/dst block
            # (on tolère le départ/arrivée, mais si ça traverse le rectangle, c'est moche)
            collides = candidate.intersects(src_rect) or candidate.intersects(dst_rect)

            if not collides:
                path = candidate
            else:
                p1_far = QPointF(p1.x() + src_out_sign * detour, p1.y())
                p2_far = QPointF(p2.x() + dst_in_sign * detour, p2.y())

                # route_y: petit décalage vertical pour éviter de repasser sur les ports
                # (tu peux aussi reprendre ta logique "above/below/between" ici)
                route_y = p1.y() if abs(p1.y() - p2.y()) < 10 else (p1.y() + p2.y()) * 0.5

                candidate2 = QPainterPath(p1)
                candidate2.lineTo(p1_far)
                candidate2.lineTo(p1_far.x(), route_y)
                candidate2.lineTo(p2_far.x(), route_y)
                candidate2.lineTo(p2_far)
                candidate2.lineTo(p2)

                # si encore collision, on force un passage au-dessus/en dessous
                if candidate2.intersects(src_rect) or candidate2.intersects(dst_rect):
                    # reprendre ton feedback chooser (above/below/between) mais sans u_turn
                    candidates_y = []
                    candidates_y.append(min(src_rect.top(), dst_rect.top()) - margin)
                    candidates_y.append(max(src_rect.bottom(), dst_rect.bottom()) + margin)
                    if src_rect.bottom() < dst_rect.top():
                        candidates_y.append((src_rect.bottom() + dst_rect.top()) * 0.5)
                    elif dst_rect.bottom() < src_rect.top():
                        candidates_y.append((dst_rect.bottom() + src_rect.top()) * 0.5)

                    route_y = min(candidates_y, key=lambda y: abs(p1.y()-y)+abs(p2.y()-y))

                    candidate2 = QPainterPath(p1)
                    candidate2.lineTo(p1_far)
                    candidate2.lineTo(p1_far.x(), route_y)
                    candidate2.lineTo(p2_far.x(), route_y)
                    candidate2.lineTo(p2_far)
                    candidate2.lineTo(p2)

                path = candidate2


        # -------------------------------------------------
        # FEEDBACK (U-turn or self-loop): route above/below/between
        # -------------------------------------------------
        else:
            candidates = []

            # above
            y_above = min(src_rect.top(), dst_rect.top()) - margin
            candidates.append(y_above)

            # below
            y_below = max(src_rect.bottom(), dst_rect.bottom()) + margin
            candidates.append(y_below)

            # between (only if there is a vertical gap)
            if src_rect.bottom() < dst_rect.top():
                candidates.append((src_rect.bottom() + dst_rect.top()) * 0.5)
            elif dst_rect.bottom() < src_rect.top():
                candidates.append((dst_rect.bottom() + src_rect.top()) * 0.5)

            route_y = min(
                candidates,
                key=lambda y: abs(p1.y() - y) + abs(p2.y() - y)
            )

            # always advance out of the source, then bridge, then approach destination from outside
            path.lineTo(p1_out)
            path.lineTo(p1_out.x(), route_y)
            path.lineTo(p2_in.x(), route_y)
            path.lineTo(p2_in)
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
