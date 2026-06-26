# ******************************************************************************
#                                  pySimBlocks
#                     Copyright (c) 2026 Université de Lille & INRIA
# ******************************************************************************

from __future__ import annotations

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QPainterPath, QPainterPathStroker, QPen
from PySide6.QtWidgets import QGraphicsPathItem


class ManualBoundaryWireItem(QGraphicsPathItem):
    """Visual-only wire for an incomplete manual group boundary."""

    def __init__(
        self,
        view,
        src_anchor,
        dst_anchor,
        *,
        group_uid: str,
        boundary_uid: str,
        side: str,
    ):
        super().__init__()
        self._view = view
        self._src_anchor = src_anchor
        self._dst_anchor = dst_anchor
        self.group_uid = group_uid
        self.boundary_uid = boundary_uid
        self.side = side
        self.setPen(QPen(view.theme.wire, 2, Qt.DashLine))
        self.setZValue(1)
        self.setFlag(QGraphicsPathItem.ItemIsSelectable, True)
        self.setAcceptedMouseButtons(Qt.LeftButton)
        self.update_position()

    def update_position(self) -> None:
        p1 = self._src_anchor()
        p2 = self._dst_anchor()
        mid = QPointF((p1.x() + p2.x()) * 0.5, p1.y())
        path = QPainterPath()
        path.moveTo(p1)
        path.lineTo(mid)
        path.lineTo(QPointF(mid.x(), p2.y()))
        path.lineTo(p2)
        self.setPath(path)

    def shape(self):
        stroker = QPainterPathStroker()
        stroker.setWidth(12)
        return stroker.createStroke(self.path())
