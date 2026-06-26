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

from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QPen, QPainterPath, QPainterPathStroker
from PySide6.QtWidgets import QGraphicsItem, QGraphicsPathItem

from pySimBlocks.gui.graphics.port_item import PortItem
from pySimBlocks.gui.models.connection_instance import ConnectionInstance


def _endpoint_view(endpoint):
    if isinstance(endpoint, PortItem):
        return endpoint.parent_block.view
    from pySimBlocks.gui.graphics.group_proxy_item import GroupProxyPortItem
    from pySimBlocks.gui.graphics.group_item import GroupBoundaryPortItem

    if isinstance(endpoint, GroupProxyPortItem):
        return endpoint.parent_proxy.view
    if isinstance(endpoint, GroupBoundaryPortItem):
        return endpoint.parent_group.view
    raise TypeError(f"Unsupported wire endpoint: {type(endpoint)!r}")


class OrthogonalRoute:
    """Store routed connection points and the segment being dragged.

    Attributes:
        points: Ordered route points in scene coordinates.
        dragged_index: Index of the segment currently being dragged.
    """

    def __init__(self, points: list[QPointF]):
        """Initialize a routed polyline.

        Args:
            points: Ordered route points in scene coordinates.

        Raises:
            None.
        """
        self.points = points
        self.dragged_index: int | None = None


class ConnectionItem(QGraphicsPathItem):
    """Render and interact with a connection between two ports.

    Attributes:
        src_port: Source port item of the connection.
        dst_port: Destination port item of the connection.
        instance: Connection model represented by this item.
        is_temporary: Whether the connection is currently incomplete.
        is_manual: Whether the route was manually adjusted.
        route: Current orthogonal route definition.
    """

    OFFSET = 8
    MARGIN = 12
    DETOUR = 8
    PICK_TOL = 10
    GRID = 5
    AXIS_EPS = 0.5
    JOG_EPS = 8.0

    def __init__(self,
                 src_port: PortItem | None,
                 dst_port: PortItem | None,
                 instance: ConnectionInstance,
                 points: list[QPointF] | None = None):
        """Initialize a connection item.

        Args:
            src_port: Source port item, if already known.
            dst_port: Destination port item, if already known.
            instance: Connection model represented by this item.
            points: Optional persisted route points.

        Raises:
            ValueError: If both ports are missing.
        """
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
        self._route_drag_active = False
        self._route_points_before_drag: list[QPointF] | None = None
        self._manual_src_redirected: bool | None = None
        self._manual_dst_redirected: bool | None = None
        self._manual_view_group_uid: str | None = None

        if points and len(points) >= 2:
            self.apply_manual_route(points)

        t = _endpoint_view(self._valid_port)


        if self.is_temporary:
            self.setFlag(QGraphicsItem.ItemIsSelectable, False)
            self.setAcceptedMouseButtons(Qt.NoButton)
            pen = QPen(t.theme.wire, 3, Qt.DashLine)
        else:
            self.setFlag(QGraphicsItem.ItemIsSelectable, True)
            self.setAcceptedMouseButtons(Qt.LeftButton)
            pen = QPen(t.theme.wire, 3, Qt.SolidLine)

        self.setPen(pen)
        self.setZValue(2)

        self.update_position()

    # --------------------------------------------------------------------------
    # Public Methods
    # --------------------------------------------------------------------------
    def update_position(self):
        """Recompute the displayed route from the current port positions."""
        if self.is_temporary:
            return

        view = self.src_port.parent_block.view
        p1 = view.connection_anchor_for_port_item(self.src_port)
        p2 = view.connection_anchor_for_port_item(self.dst_port)

        if self._route_drag_active:
            if self.route and len(self.route.points) >= 2:
                self.route.points[0] = p1
                self.route.points[-1] = p2
                self._apply_route(self.route.points, simplify=False)
            return

        if self.is_manual and self.route and len(self.route.points) >= 2:
            if self._manual_anchor_context_matches():
                self.route.points[0] = p1
                self.route.points[-1] = p2
                self._apply_route(self.route.points, simplify=False)
                return
            self.is_manual = False

        pts = self._compute_auto_route(p1, p2)
        self.route = OrthogonalRoute(pts)
        self.is_manual = False
        self._manual_src_redirected = None
        self._manual_dst_redirected = None
        self._manual_view_group_uid = None
        self._apply_route(self.route.points)

    def update_temp_position(self, scene_pos: QPointF):
        """Update the temporary route endpoint while dragging.

        Args:
            scene_pos: Current mouse position in scene coordinates.
        """
        p1 = self._valid_port.connection_anchor()
        self._apply_route([p1, scene_pos], simplify=False)

    def apply_manual_route(self, points: list[QPointF]):
        """Apply a persisted manual route to the connection.

        Args:
            points: Route points in scene coordinates.
        """
        self.route = OrthogonalRoute(points)
        self.is_manual = True
        self._capture_manual_anchor_context()
        self._apply_route(self.route.points)

    def invalidate_manual_route(self):
        """Discard any manual route so the next update recomputes it."""
        self.is_manual = False
        self.route = None
        self._manual_src_redirected = None
        self._manual_dst_redirected = None
        self._manual_view_group_uid = None

    def segment_at(self, scene_pos: QPointF) -> int | None:
        """Return the route segment index located near the given scene point.

        Args:
            scene_pos: Scene position to test.

        Returns:
            Index of the matching segment, or None if none is close enough.
        """
        if not self.route:
            return None

        pts = self.route.points
        for i in range(len(pts) - 1):
            a, b = pts[i], pts[i + 1]

            if abs(a.x() - b.x()) < self.AXIS_EPS:  # vertical
                if abs(scene_pos.x() - a.x()) < self.PICK_TOL \
                   and min(a.y(), b.y()) - self.PICK_TOL <= scene_pos.y() <= max(a.y(), b.y()) + self.PICK_TOL:
                    return i

            elif abs(a.y() - b.y()) < self.AXIS_EPS:  # horizontal
                if abs(scene_pos.y() - a.y()) < self.PICK_TOL \
                   and min(a.x(), b.x()) - self.PICK_TOL <= scene_pos.x() <= max(a.x(), b.x()) + self.PICK_TOL:
                    return i
        return None

    def shape(self):
        """Return an enlarged hit shape so connections are easier to select.

        Returns:
            Stroke path used for hit testing.
        """
        stroker = QPainterPathStroker()
        stroker.setWidth(12)
        return stroker.createStroke(self.path())

    def mousePressEvent(self, event):
        """Start manual segment dragging with the left mouse button."""
        if event.button() == Qt.LeftButton:
            idx = self.segment_at(event.scenePos())
            if idx is not None:
                if self.route is None:
                    self.update_position()
                if self.route is None:
                    super().mousePressEvent(event)
                    return
                self._route_points_before_drag = [
                    QPointF(point) for point in self.route.points
                ]
                self.route.dragged_index = idx
                self.is_manual = True
                self._route_drag_active = True
                self.grabMouse()
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Move the selected orthogonal segment during manual route editing."""
        if not self.route or self.route.dragged_index is None:
            super().mouseMoveEvent(event)
            return

        if not (event.buttons() & Qt.LeftButton):
            return

        i = self.route.dragged_index
        points = self.route.points
        if i < 0 or i + 1 >= len(points):
            self.route.dragged_index = None
            self._route_drag_active = False
            self.ungrabMouse()
            return

        a = points[i]
        b = points[i + 1]
        pos = event.scenePos()

        if abs(a.x() - b.x()) < self.AXIS_EPS:  # vertical segment
            x = self._snap(pos.x())
            points[i] = QPointF(x, a.y())
            points[i + 1] = QPointF(x, b.y())

        elif abs(a.y() - b.y()) < self.AXIS_EPS:  # horizontal segment
            y = self._snap(pos.y())
            points[i] = QPointF(a.x(), y)
            points[i + 1] = QPointF(b.x(), y)

        else:
            return

        self._apply_route(points, simplify=False)

    def mouseReleaseEvent(self, event):
        """Finish manual segment dragging."""
        was_dragging = self._route_drag_active
        if self.route:
            self.route.dragged_index = None
        self._route_drag_active = False
        if was_dragging:
            self.ungrabMouse()
        super().mouseReleaseEvent(event)
        if was_dragging and event.button() == Qt.LeftButton and self.route is not None:
            self._apply_route(self.route.points)
            self._capture_manual_anchor_context()
            view = self.src_port.parent_block.view
            new_points = [QPointF(point) for point in self.route.points]
            view.on_connection_route_edited(
                self,
                self._route_points_before_drag,
                new_points,
            )
        self._route_points_before_drag = None


    # --------------------------------------------------------------------------
    # Private Methods
    # --------------------------------------------------------------------------

    def _anchor_redirected(self, port_item: PortItem) -> bool:
        """Return whether the current view routes this port through a group border or proxy."""
        view = port_item.parent_block.view
        redirected = view.connection_anchor_for_port_item(port_item)
        direct = port_item.connection_anchor()
        return (
            abs(redirected.x() - direct.x()) > 0.5
            or abs(redirected.y() - direct.y()) > 0.5
        )

    def _capture_manual_anchor_context(self) -> None:
        """Remember view level and anchor redirection when the route was edited."""
        view = self.src_port.parent_block.view
        self._manual_view_group_uid = view.current_view_group_uid
        self._manual_src_redirected = self._anchor_redirected(self.src_port)
        self._manual_dst_redirected = self._anchor_redirected(self.dst_port)

    def _manual_anchor_context_matches(self) -> bool:
        """Return whether the current view matches the one used when the route was edited."""
        view = self.src_port.parent_block.view
        if view.current_view_group_uid != self._manual_view_group_uid:
            return False
        src_redirected = self._anchor_redirected(self.src_port)
        dst_redirected = self._anchor_redirected(self.dst_port)
        if self._manual_src_redirected is None or self._manual_dst_redirected is None:
            return not src_redirected and not dst_redirected
        return (
            self._manual_src_redirected == src_redirected
            and self._manual_dst_redirected == dst_redirected
        )

    def _compute_auto_route(self, p1: QPointF, p2: QPointF) -> list[QPointF]:
        """Compute an orthogonal route between two port anchors."""
        src_rect = self._routing_rect_for_port(self.src_port)
        dst_rect = self._routing_rect_for_port(self.dst_port)

        src_out_sign = self._wire_side_sign(p1, src_rect)
        dst_in_sign = self._wire_side_sign(p2, dst_rect)

        p1_out = QPointF(p1.x() + src_out_sign * self.OFFSET, p1.y())
        p2_in = QPointF(p2.x() + dst_in_sign * self.OFFSET, p2.y())

        same_block = self.src_port.parent_block is self.dst_port.parent_block
        u_turn = ((p2_in.x() - p1_out.x()) * src_out_sign) < 0
        is_feedback = same_block or u_turn

        if not is_feedback:
            if abs(p1.y() - p2.y()) < self.AXIS_EPS:
                straight = [p1, p1_out, p2_in, p2]
                path = self._path_from(straight)
                if not (path.intersects(src_rect) or path.intersects(dst_rect)):
                    return straight

            if abs(p1.y() - p2.y()) <= self.JOG_EPS:
                candidate = [p1, p1_out, QPointF(p2.x(), p1.y()), p2]
            else:
                mid_x = (p1_out.x() + p2_in.x()) * 0.5
                candidate = [
                    p1, p1_out,
                    QPointF(mid_x, p1.y()),
                    QPointF(mid_x, p2.y()),
                    p2_in, p2
                ]

            path = self._path_from(candidate)
            if not (path.intersects(src_rect) or path.intersects(dst_rect)):
                return self._simplify_orthogonal_route(candidate)

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

        if src_rect.left() <= p2_in.x() <= src_rect.right():
            approach_x = (
                src_rect.left() - self.DETOUR
                if dst_in_sign < 0
                else src_rect.right() + self.DETOUR
            )
            return self._simplify_orthogonal_route(
                [
                    p1,
                    p1_out,
                    QPointF(p1_out.x(), route_y),
                    QPointF(approach_x, route_y),
                    QPointF(approach_x, p2.y()),
                    p2,
                ]
            )

        return self._simplify_orthogonal_route(
            [
                p1, p1_out,
                QPointF(p1_out.x(), route_y),
                QPointF(p2_in.x(), route_y),
                p2_in, p2
            ]
        )

    def _wire_side_sign(self, anchor: QPointF, rect: QRectF) -> int:
        """Return -1 when the anchor is on the left edge, +1 on the right."""
        dist_left = abs(anchor.x() - rect.left())
        dist_right = abs(anchor.x() - rect.right())
        return -1 if dist_left <= dist_right else 1

    def _routing_rect_for_port(self, port_item: PortItem) -> QRectF:
        """Return the scene rectangle used for obstacle avoidance."""
        view = port_item.parent_block.view
        return view.routing_rect_for_port_item(port_item)

    def _wire_length(self, points: list[QPointF]) -> float:
        total = 0.0
        for index in range(len(points) - 1):
            a = points[index]
            b = points[index + 1]
            total += abs(a.x() - b.x()) + abs(a.y() - b.y())
        return total

    def _simplify_orthogonal_route(self, points: list[QPointF]) -> list[QPointF]:
        if len(points) <= 2:
            return [QPointF(point) for point in points]

        simplified = [QPointF(points[0])]
        for index in range(1, len(points) - 1):
            prev_pt = simplified[-1]
            current = points[index]
            next_pt = points[index + 1]
            same_vertical = (
                abs(prev_pt.x() - current.x()) < self.AXIS_EPS
                and abs(current.x() - next_pt.x()) < self.AXIS_EPS
            )
            same_horizontal = (
                abs(prev_pt.y() - current.y()) < self.AXIS_EPS
                and abs(current.y() - next_pt.y()) < self.AXIS_EPS
            )
            if same_vertical or same_horizontal:
                continue
            simplified.append(QPointF(current))
        simplified.append(QPointF(points[-1]))
        return simplified

    def _snap(self, v: float) -> float:
        """Snap a scalar coordinate to the routing grid."""
        return round(v / self.GRID) * self.GRID

    def _apply_route(self, points: list[QPointF], *, simplify: bool = True):
        """Apply a route by building and setting the corresponding path."""
        cleaned = (
            self._simplify_orthogonal_route(points)
            if simplify
            else [QPointF(point) for point in points]
        )
        if len(cleaned) < 2:
            return
        path = QPainterPath(cleaned[0])
        for point in cleaned[1:]:
            path.lineTo(point)
        self.setPath(path)
        if self.route is not None:
            self.route.points = cleaned

    def _path_from(self, pts: list[QPointF]) -> QPainterPath:
        """Build a painter path from an ordered list of route points."""
        p = QPainterPath(pts[0])
        for pt in pts[1:]:
            p.lineTo(pt)
        return p
