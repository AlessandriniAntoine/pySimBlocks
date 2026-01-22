# ******************************************************************************
#                                 pySimBlocks                                 
#                Copyright (c) 2026 The pySimBlocks Authors               
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
from PySide6.QtGui import QPen, QPainterPath

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

    def update_position(self):
        p1 = self.port1.scenePos()
        p2 = self.port2.scenePos()

        dx = abs(p2.x() - p1.x()) * 0.5

        c1 = QPointF(p1.x() + dx, p1.y())
        c2 = QPointF(p2.x() - dx, p2.y())

        path = QPainterPath(p1)
        path.cubicTo(c1, c2, p2)
        self.setPath(path)

    def remove(self):
        if self in self.port1.connections:
            self.port1.connections.remove(self)
        if self in self.port2.connections:
            self.port2.connections.remove(self)
