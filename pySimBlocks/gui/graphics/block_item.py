from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsItem, QStyle
from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor, QPen

from pySimBlocks.gui.dialogs.block_dialog import BlockDialog
from pySimBlocks.gui.graphics.port_item import PortItem
from pySimBlocks.gui.model.block_instance import BlockInstance


class BlockItem(QGraphicsRectItem):
    WIDTH = 120
    HEIGHT = 60

    def __init__(self, instance: BlockInstance, pos, view):
        super().__init__(0, 0, self.WIDTH, self.HEIGHT)
        self.view = view
        self.instance = instance

        self.setPos(pos)
        self.setFlag(QGraphicsRectItem.ItemIsMovable)
        self.setFlag(QGraphicsRectItem.ItemIsSelectable)
        self.setFlag(QGraphicsRectItem.ItemSendsScenePositionChanges)

        # Ports
        self.port_items = []
        self.instance.resolve_ports()
        for port in self.instance.ports:
            item = PortItem(port, self)
            self.port_items.append(item)
        self._layout_ports()


    def paint(self, painter, option, widget=None):
        # --- background ---
        if option.state & QStyle.State_Selected:
            painter.setBrush(QColor("#88C0D0"))
            painter.setPen(QPen(QColor("#2E3440"), 2))
        else:
            painter.setBrush(QColor("#E6F2FF"))
            painter.setPen(QPen(QColor("#4C566A"), 1))

        painter.drawRect(self.rect())

        # --- text ---
        painter.setPen(QColor("#2E3440"))
        painter.drawText(self.rect(), Qt.AlignCenter, self.instance.name)

    def mouseDoubleClickEvent(self, event):
        dialog = BlockDialog(self, readonly=False)
        dialog.exec()
        self.update()
        event.accept()

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            for port in self.port_items:
                for c in port.connections:
                    c.update_position()
        return super().itemChange(change, value)

    def remove_all_connections(self):
        for port in self.port_items:
            for conn in port.connections[:]:
                conn.remove()

    def get_port_item(self, name:str) -> PortItem | None:
        for port in self.port_items:
            if port.instance.name == name:
                return port


    def refresh_ports(self):
        for item in self.port_items:
            self.scene().removeItem(item)

        self.port_items.clear()
        self.instance.resolve_ports()

        for port in self.instance.ports:
            self.port_items.append(PortItem(port, self))

        self._layout_ports()

    def _layout_ports(self):
        inputs = [p for p in self.port_items if p.instance.direction == "input"]
        outputs = [p for p in self.port_items if p.instance.direction == "output"]

        self._layout_side(inputs, x=0)
        self._layout_side(outputs, x=self.WIDTH)

    def _layout_side(self, ports, x):
        if not ports:
            return

        step = self.HEIGHT / (len(ports) + 1)

        for i, port in enumerate(ports, start=1):
            port.setPos(x, i * step)
            port.update_label_position()
