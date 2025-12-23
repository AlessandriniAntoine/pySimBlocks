from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem
from PySide6.QtCore import Qt, QMimeData
from PySide6.QtGui import QDrag

class BlockList(QTreeWidget):
    def __init__(self, get_categories, get_blocks):
        super().__init__()
        self.setHeaderHidden(True)
        self.setDragEnabled(True)

        self.get_categories = get_categories
        self.get_blocks = get_blocks

        for category in self.get_categories():
            operators = QTreeWidgetItem(self, [category])
            operators.setExpanded(False)
            for block_type in self.get_blocks(category):
                block = QTreeWidgetItem(operators, [block_type])
                block.setData(0, Qt.UserRole, (category, block_type))

    def startDrag(self, supportedActions):
        item = self.currentItem()
        if not item or item.childCount() > 0:
            return
        category, block_type = item.data(0, Qt.UserRole)
        mime = QMimeData()
        mime.setText(f"{category}:{block_type}")

        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.exec(Qt.MoveAction)
