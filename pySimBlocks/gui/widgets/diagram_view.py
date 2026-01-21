from typing import Callable
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPainter

from pySimBlocks.gui.graphics.block_item import BlockItem
from pySimBlocks.gui.graphics.connection_item import ConnectionItem
from pySimBlocks.gui.graphics.port_item import PortItem
from pySimBlocks.gui.model.block_instance import BlockInstance
from pySimBlocks.gui.model.connection_instance import ConnectionInstance
from pySimBlocks.gui.model.project_state import ProjectState
from pySimBlocks.tools.blocks_registry import BlockMeta



class DiagramView(QGraphicsView):
    def __init__(self, 
                 resolve_block_meta: Callable[[str, str], BlockMeta], 
                 project_state:ProjectState
    ):
        super().__init__()
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setAcceptDrops(True)
        self.setRenderHint(QPainter.Antialiasing)

        self.pending_port: PortItem | None = None
        self.copied_block = None
        self.resolve_block_meta = resolve_block_meta
        self.project_state = project_state
        self.block_items: dict[str, BlockItem] = {}

        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.RubberBandDrag)


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
        self.block_items[instance.uid] = block_item
        event.acceptProposedAction()


    def start_connection(self, port: PortItem):
        self.pending_port = port


    def finish_connection(self, port: PortItem):
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
                self.block_items[instance.uid] = block_item
            return

        # DELETE
        if event.key() == Qt.Key_Delete:
            self.delete_selected()
            return

        # ZOOM IN / OUT
        if event.key() in (Qt.Key_Plus, Qt.Key_Equal) and event.modifiers() & Qt.ControlModifier:
            self.scale_view(1.15)
            return

        if event.key() == Qt.Key_Minus and event.modifiers() & Qt.ControlModifier:
            self.scale_view(1 / 1.15)
            return


        super().keyPressEvent(event)


    def delete_selected(self):
        for item in self.scene.selectedItems():
            if isinstance(item, BlockItem):
                del self.block_items[item.instance.uid]
                self.project_state.remove_block(item.instance)
                item.remove_all_connections()
                self.scene.removeItem(item)

            elif isinstance(item, ConnectionItem):
                self.project_state.remove_connection(item.instance)
                item.remove()
                self.scene.removeItem(item)


    def clear_scene(self):
        for item in list(self.scene.items()):
            self.scene.removeItem(item)
            del item
        self.block_items.clear()
        self.pending_port = None


    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            zoom_factor = 1.15
            if event.angleDelta().y() > 0:
                self.scale_view(zoom_factor)
            else:
                self.scale_view(1 / zoom_factor)
            event.accept()
        else:
            super().wheelEvent(event)


    def scale_view(self, factor):
        current_scale = self.transform().m11()
        min_scale, max_scale = 0.2, 5.0

        new_scale = current_scale * factor
        if min_scale <= new_scale <= max_scale:
            self.scale(factor, factor)
