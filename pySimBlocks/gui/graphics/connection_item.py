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

from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPen, QPainterPath, QPainterPathStroker
from PySide6.QtWidgets import QGraphicsItem, QGraphicsPathItem

from pySimBlocks.gui.graphics.port_item import PortItem
from pySimBlocks.gui.model.connection_instance import ConnectionInstance


class OrthogonalRoute:
    def __init__(self, points: list[QPointF]):
        self.points = points
        self.dragged_index: int | None = None


class ConnectionItem(QGraphicsPathItem):
    OFFSET = 8
    MARGIN = 12
    DETOUR = 8
    PICK_TOL = 6
    GRID = 5

    def __init__(self,
                 src_port: PortItem | None,
                 dst_port: PortItem | None,
                 instance: ConnectionInstance,
                 points: list[QPointF] | None = None):
        super().__init__()

        if src_port is None and dst_port is None:
            raise ValueError("At least one of the ports must be provided")

        self.src_port = src_port
        self.dst_port = dst_port
        self.instance = instance
        self.is_temporary = (src_port is None) or (dst_port is None)
        self._valid_port = src_port if src_port is not None else dst_port
        self.is_manual: bool = False
        self.route: OrthogonalRoute | None = None

        if points and len(points) >= 2:
            self.apply_manual_route(points)

        t = self._valid_port.parent_block.view.theme


        if self.is_temporary:
            self.setFlag(QGraphicsItem.ItemIsSelectable, False)
            self.setAcceptedMouseButtons(Qt.NoButton)
            pen = QPen(t.wire, 3, Qt.DashLine)
        else:
            self.setFlag(QGraphicsItem.ItemIsSelectable, True)
            self.setAcceptedMouseButtons(Qt.LeftButton)
            pen = QPen(t.wire, 3, Qt.SolidLine)

        self.setPen(pen)
        self.setZValue(1)

        self.update_position()

    # --------------------------------------------------------------------------
    #  Position methods
    # --------------------------------------------------------------------------
    def update_position(self):
        if self.is_temporary:
            return

        p1 = self.src_port.connection_anchor()
        p2 = self.dst_port.connection_anchor()
        if self.is_manual and self.route and len(self.route.points) >= 2:
            self.route.points[0] = p1
            self.route.points[-1] = p2
            self._apply_route(self.route.points)
            return

        pts = self._compute_auto_route(p1, p2)
        self.route = OrthogonalRoute(pts)
        self._apply_route(self.route.points)

    # ------------------------------------------------------------------
    def update_temp_position(self, scene_pos: QPointF):
        p1 = self._valid_port.connection_anchor()
        pts = [p1, scene_pos]
        self._apply_route(pts)

    # --------------------------------------------------------------------------
    # Routing methods
    # --------------------------------------------------------------------------
    def apply_manual_route(self, points: list[QPointF]):
        self.route = OrthogonalRoute(points)
        self.is_manual = True
        self._apply_route(self.route.points)

    # ------------------------------------------------------------------
    def invalidate_manual_route(self):
        """
        Called when a connected block moves: manual routing is discarded and
        next update_position() will fully recompute the orthogonal route.
        """
        self.is_manual = False
        self.route = None

    # ------------------------------------------------------------------
    def _compute_auto_route(self, p1: QPointF, p2: QPointF) -> list[QPointF]:
        src_block = self.src_port.parent_block
        dst_block = self.dst_port.parent_block

        # Use the visual block rect (not selection handle hit area) for routing.
        src_rect = src_block.mapRectToScene(src_block.rect())
        dst_rect = dst_block.mapRectToScene(dst_block.rect())

        src_out_sign = 1 if not self.src_port.is_on_left_side else -1
        dst_in_sign = -1 if self.dst_port.is_on_left_side else 1

        p1_out = QPointF(p1.x() + src_out_sign * self.OFFSET, p1.y())
        p2_in = QPointF(p2.x() + dst_in_sign * self.OFFSET, p2.y())

        same_block = src_block is dst_block
        u_turn = ((p2_in.x() - p1_out.x()) * src_out_sign) < 0
        is_feedback = same_block or u_turn

        if not is_feedback:
            mid_x = (p1_out.x() + p2_in.x()) * 0.5
            candidate = [
                p1, p1_out,
                QPointF(mid_x, p1.y()),
                QPointF(mid_x, p2.y()),
                p2_in, p2
            ]

            path = self._path_from(candidate)
            if not (path.intersects(src_rect) or path.intersects(dst_rect)):
                return candidate

        # fallback / feedback routing
        candidates_y = [
            min(src_rect.top(), dst_rect.top()) - self.MARGIN,
            max(src_rect.bottom(), dst_rect.bottom()) + self.MARGIN
        ]

        if src_rect.bottom() < dst_rect.top():
            candidates_y.append((src_rect.bottom() + dst_rect.top()) * 0.5)
        elif dst_rect.bottom() < src_rect.top():
            candidates_y.append((dst_rect.bottom() + src_rect.top()) * 0.5)

        route_y = min(
            candidates_y,
            key=lambda y: abs(p1.y() - y) + abs(p2.y() - y)
        )

        return [
            p1, p1_out,
            QPointF(p1_out.x(), route_y),
            QPointF(p2_in.x(), route_y),
            p2_in, p2
        ]

    # ------------------------------------------------------------------
    def _snap(self, v: float) -> float:
        return round(v / self.GRID) * self.GRID

    # --------------------------------------------------------------------------
    # Path methods
    # --------------------------------------------------------------------------
    def _apply_route(self, points: list[QPointF]):
        path = QPainterPath(points[0])
        for p in points[1:]:
            path.lineTo(p)
        self.setPath(path)

    # ------------------------------------------------------------------
    def _path_from(self, pts: list[QPointF]) -> QPainterPath:
        p = QPainterPath(pts[0])
        for pt in pts[1:]:
            p.lineTo(pt)
        return p

    # --------------------------------------------------------------------------
    # Interaction (segment dragging)
    # --------------------------------------------------------------------------
    def segment_at(self, scene_pos: QPointF) -> int | None:
        if not self.route:
            return None

        pts = self.route.points
        for i in range(len(pts) - 1):
            a, b = pts[i], pts[i + 1]

            if a.x() == b.x():  # vertical
                if abs(scene_pos.x() - a.x()) < self.PICK_TOL \
                   and min(a.y(), b.y()) <= scene_pos.y() <= max(a.y(), b.y()):
                    return i

            if a.y() == b.y():  # horizontal
                if abs(scene_pos.y() - a.y()) < self.PICK_TOL \
                   and min(a.x(), b.x()) <= scene_pos.x() <= max(a.x(), b.x()):
                    return i
        return None

    # --------------------------------------------------------------
    def shape(self):
        """
        Override the default shape to make it easier to click on the connection.
        """
        stroker = QPainterPathStroker()
        stroker.setWidth(6)  # zone cliquable (px)
        return stroker.createStroke(self.path())

    # --------------------------------------------------------------------------
    # Events methods
    # --------------------------------------------------------------------------
    def mousePressEvent(self, event):
        idx = self.segment_at(event.scenePos())
        if idx is not None:
            self.route.dragged_index = idx
            self.is_manual = True
            event.accept()
        else:
            super().mousePressEvent(event)

    # ------------------------------------------------------------------
    def mouseMoveEvent(self, event):
        if not self.route or self.route.dragged_index is None:
            return

        i = self.route.dragged_index
        a = self.route.points[i]
        b = self.route.points[i + 1]
        pos = event.scenePos()

        if a.x() == b.x():  # vertical segment
            x = self._snap(pos.x())
            self.route.points[i]     = QPointF(x, a.y())
            self.route.points[i + 1] = QPointF(x, b.y())

        elif a.y() == b.y():  # horizontal segment
            y = self._snap(pos.y())
            self.route.points[i]     = QPointF(a.x(), y)
            self.route.points[i + 1] = QPointF(b.x(), y)

        self._apply_route(self.route.points)

    # ------------------------------------------------------------------
    def mouseReleaseEvent(self, event):
        if self.route:
            self.route.dragged_index = None
        super().mouseReleaseEvent(event)
