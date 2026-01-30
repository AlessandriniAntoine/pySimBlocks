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

from PySide6.QtWidgets import QGraphicsView, QGraphicsScene
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPainter

from pySimBlocks.gui.graphics.block_item import BlockItem
from pySimBlocks.gui.graphics.connection_item import ConnectionItem
from pySimBlocks.gui.graphics.port_item import PortItem
from pySimBlocks.gui.model.block_instance import BlockInstance
from pySimBlocks.gui.model.connection_instance import ConnectionInstance

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pySimBlocks.gui.services.project_controller import ProjectController


class DiagramView(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.diagram_scene = QGraphicsScene(self)
        self.setScene(self.diagram_scene)
        self.setAcceptDrops(True)
        self.setRenderHint(QPainter.Antialiasing)

        self.pending_port: PortItem | None = None
        self.copied_block: BlockItem | None = None
        self.project_controller: "ProjectController" | None
        self.block_items: dict[str, BlockItem] = {}
        self.connections: dict[ConnectionInstance, ConnectionItem] = {}

        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.RubberBandDrag)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        event.acceptProposedAction()

    def dropEvent(self, event):
        self.drop_event_pos = self.mapToScene(event.position().toPoint())
        category, block_type = event.mimeData().text().split(":")
        self.project_controller.add_block(category, block_type)
        event.acceptProposedAction()

    def add_block(self, block_instance: BlockInstance):
        block_item = BlockItem(block_instance, self.drop_event_pos, self)
        self.diagram_scene.addItem(block_item)
        self.block_items[block_instance.uid] = block_item

    def remove_block(self, block_instance: BlockInstance):
        block_item = self.block_items[block_instance.uid]
        self.diagram_scene.removeItem(block_item)
        self.block_items.pop(block_instance.uid, None)

    def add_connecton(self, connection_instance: ConnectionInstance):
        src_port_item = self.get_block_item_from_instance(connection_instance.src_block()).get_port_item(connection_instance.src_port.name)
        dst_port_item = self.get_block_item_from_instance(connection_instance.dst_block()).get_port_item(connection_instance.dst_port.name)
        connection_item = ConnectionItem(src_port_item, dst_port_item, connection_instance)
        self.connections[connection_instance] = connection_item
        self.diagram_scene.addItem(connection_item)

    def remove_connection(self, connection_instance: ConnectionInstance):
        connection_item = self.connections.pop(connection_instance, None)
        if connection_item:
            self.diagram_scene.removeItem(connection_item)

    def get_block_item_from_instance(self, block_instance: BlockInstance) -> BlockItem | None:
        return self.block_items.get(block_instance.uid)
    
    def create_connection_event(self, port: PortItem):
        if not self.pending_port:
            self.pending_port = port
            return
        
        self.project_controller.add_connection(self.pending_port.instance, port.instance)
        self.pending_port = None

    def on_block_moved(self, block_item: BlockItem):
        for conn_inst, conn_item in self.connections.items():
            if conn_inst.is_block_involved(block_item.instance):
                conn_item.update_position()

    def keyPressEvent(self, event):
        # COPY
        if event.key() == Qt.Key_C and event.modifiers() & Qt.ControlModifier:
            selected = [i for i in self.diagram_scene.selectedItems() if isinstance(i, BlockItem)]
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
                self.project_controller.add_block(instance)
                block_item = BlockItem(instance, pos, self)
                self.diagram_scene.addItem(block_item)
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
        for item in self.diagram_scene.selectedItems():
            if isinstance(item, BlockItem):
                self.project_controller.remove_block(item.instance)

            elif isinstance(item, ConnectionItem):
                self.project_controller.remove_connection(item.instance)

    def clear_scene(self):

        for block in list(self.block_items.values()):
            self.project_controller.remove_block(block.instance)
        
        for connection in list(self.connections.values()):
            self.project_controller.remove_connection(connection.instance)

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
