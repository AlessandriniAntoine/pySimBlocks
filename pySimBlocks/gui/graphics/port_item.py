from PySide6.QtWidgets import  QGraphicsEllipseItem, QGraphicsTextItem, QGraphicsItem
from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor, QPen, QFont

from pySimBlocks.gui.graphics.connection_item import ConnectionItem
from pySimBlocks.gui.model.port_instance import PortInstance

class PortItem(QGraphicsEllipseItem):
    R = 6

    def __init__(self, 
                instance: PortInstance, 
                parent_block, # BlockItem, can't import type due to circular import
    ):
        super().__init__(
            -self.R, -self.R, 2 * self.R, 2 * self.R, parent_block
        )

        self.instance = instance
        self.parent_block = parent_block
        self.connections: list[ConnectionItem] = []

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
        view = self.parent_block.view
        if view.pending_port is None:
            view.start_connection(self)
        else:
            view.finish_connection(self)
        event.accept()

    def is_compatible(self, other: 'PortItem'):
        return self.instance.direction != other.instance.direction

    def can_accept_connection(self) -> bool:
        if self.instance.direction == "input":
            return len(self.connections) == 0
        return True

    def add_connection(self, conn: ConnectionItem):
        self.connections.append(conn)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemScenePositionHasChanged:
            for c in self.connections:
                c.update_position()
            self.update_label_position()

        return super().itemChange(change, value)
