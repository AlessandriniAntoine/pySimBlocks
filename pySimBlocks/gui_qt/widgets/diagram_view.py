import re
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPainter

from pySimBlocks.gui_qt.graphics.block_item import BlockItem
from pySimBlocks.gui_qt.graphics.connection_item import ConnectionItem
from pySimBlocks.gui_qt.model.block_instance import BlockInstance
from pySimBlocks.gui_qt.model.connection_instance import ConnectionInstance
from pySimBlocks.gui_qt.model.project_state import ProjectState



class DiagramView(QGraphicsView):
    def __init__(self, resolve_block_meta, project_state:ProjectState):
        super().__init__()
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setAcceptDrops(True)
        self.setRenderHint(QPainter.Antialiasing)

        self.pending_port = None
        self.copied_block = None
        self.resolve_block_meta = resolve_block_meta
        self.project_state = project_state

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        event.acceptProposedAction()

    def dropEvent(self, event):
        pos = self.mapToScene(event.position().toPoint())
        category, block_type = event.mimeData().text().split(":")
        meta = self.resolve_block_meta(category, block_type)

        instance = BlockInstance(meta)
        self.project_state.add_block(instance)
        block_item = BlockItem(instance, pos, self)

        self.scene.addItem(block_item)
        event.acceptProposedAction()

    def start_connection(self, port):
        self.pending_port = port


    def finish_connection(self, port):
        if self.pending_port is None:
            return

        p1, p2 = self.pending_port, port
        if not p1.is_compatible(p2):
            self.pending_port = None
            return

        # Determine source / destination by port type
        if p1.instance.direction == "output" and p2.instance.direction == "input":
            src_port, dst_port = p1, p2
        elif p1.instance.direction == "input" and p2.instance.direction == "output":
            src_port, dst_port = p2, p1
        else:
            self.pending_port = None
            return

        if not dst_port.can_accept_connection():
            self.pending_port = None
            return

        # Create model connection
        conn_inst = ConnectionInstance(
            src_block=src_port.parent_block.instance,
            src_port=src_port.instance.name,
            dst_block=dst_port.parent_block.instance,
            dst_port=dst_port.instance.name,
        )
        self.project_state.add_connection(conn_inst)
        conn_item = ConnectionItem(src_port, dst_port, conn_inst)
        self.scene.addItem(conn_item)
        src_port.add_connection(conn_item)
        dst_port.add_connection(conn_item)
        self.pending_port = None


    def keyPressEvent(self, event):
        # COPY
        if event.key() == Qt.Key_C and event.modifiers() & Qt.ControlModifier:
            selected = [i for i in self.scene.selectedItems() if isinstance(i, BlockItem)]
            if selected:
                self.copied_block = selected[0]
            return

        # PASTE
        if event.key() == Qt.Key_V and event.modifiers() & Qt.ControlModifier:
            if self.copied_block:
                pos = self.copied_block.pos() + QPointF(30, 30)
                category = self.copied_block.instance.meta.category
                block_type = self.copied_block.instance.meta.type
                meta = self.resolve_block_meta(category, block_type)
                instance = BlockInstance(meta)
                self.project_state.add_block(instance)
                block_item = BlockItem(instance, pos, self)
                self.scene.addItem(block_item)
            return

        # DELETE
        if event.key() == Qt.Key_Delete:
            self.delete_selected()
            return

        super().keyPressEvent(event)

    def delete_selected(self):
        for item in self.scene.selectedItems():
            if isinstance(item, BlockItem):
                self.project_state.remove_block(item.instance)
                item.remove_all_connections()
                self.scene.removeItem(item)

            elif isinstance(item, ConnectionItem):
                self.project_state.remove_connection(item.instance)
                item.remove()
                self.scene.removeItem(item)
