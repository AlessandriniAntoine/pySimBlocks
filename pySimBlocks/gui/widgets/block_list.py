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

from typing import Callable
from PySide6.QtWidgets import QLineEdit, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget
from PySide6.QtCore import Qt, QMimeData
from PySide6.QtGui import QDrag

from pySimBlocks.gui.blocks.block_meta import BlockMeta
from pySimBlocks.gui.dialogs.block_dialog import BlockDialog
from pySimBlocks.gui.models.block_instance import BlockInstance

class _PreviewBlock:
    """Minimal preview wrapper used by the block dialog."""

    def __init__(self, instance):
        """Initialize the preview wrapper."""
        self.instance = instance

    def refresh_ports(self):
        """No-op refresh hook for the preview block."""
        pass


class _BlockTree(QTreeWidget):
    """Tree widget listing block categories and block types."""

    def __init__(self,
                 get_categories: Callable[[], list[str]],
                 get_blocks: Callable[[str], list[str]],
                 resolve_block_meta: Callable[[str, str], BlockMeta]):
        """Initialize the block tree.

        Args:
            get_categories: Callable returning available block categories.
            get_blocks: Callable returning block types for a category.
            resolve_block_meta: Callable resolving block metadata from names.

        Raises:
            None.
        """
        super().__init__()
        self.setHeaderHidden(True)
        self.setDragEnabled(True)

        self.get_categories = get_categories
        self.get_blocks = get_blocks
        self.resolve_block_meta = resolve_block_meta

        for category in self.get_categories():
            operators = QTreeWidgetItem(self, [category])
            operators.setExpanded(False)
            for block_type in self.get_blocks(category):
                block = QTreeWidgetItem(operators, [block_type])
                block.setData(0, Qt.UserRole, (category, block_type))

        self.itemDoubleClicked.connect(self.on_item_double_clicked)


    # --------------------------------------------------------------------------
    # Public Methods
    # --------------------------------------------------------------------------

    def startDrag(self, supportedActions):
        """Start a drag operation for the currently selected block item."""
        item = self.currentItem()
        if not item or item.childCount() > 0:
            return
        category, block_type = item.data(0, Qt.UserRole)
        mime = QMimeData()
        mime.setText(f"{category}:{block_type}")

        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.exec(Qt.MoveAction)


    def on_item_double_clicked(self, item, column):
        """Open a read-only preview dialog for a leaf block item."""
        if item.childCount() > 0:
            return

        data = item.data(0, Qt.UserRole)
        if not data:
            return

        category, block_type = data

        meta = self.resolve_block_meta(category, block_type)

        instance = BlockInstance(meta=meta)

        dialog = BlockDialog(_PreviewBlock(instance), readonly=True)
        dialog.exec()


class BlockList(QWidget):
    """Sidebar widget listing blocks and filtering them by search text.

    Attributes:
        search: Search field used to filter categories and block names.
        tree: Tree widget showing available blocks grouped by category.
    """

    def __init__(self,
                 get_categories: Callable[[], list[str]],
                 get_blocks: Callable[[str], list[str]],
                 resolve_block_meta: Callable[[str, str], BlockMeta]):
        """Initialize the block list widget.

        Args:
            get_categories: Callable returning available block categories.
            get_blocks: Callable returning block types for a category.
            resolve_block_meta: Callable resolving block metadata from names.

        Raises:
            None.
        """
        super().__init__()

        self.search = QLineEdit(self)
        self.search.setPlaceholderText("Search by category or block name...")

        self.tree = _BlockTree(get_categories, get_blocks, resolve_block_meta)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addWidget(self.search)
        layout.addWidget(self.tree)

        self.search.textChanged.connect(self._apply_filter)


    # --------------------------------------------------------------------------
    # Private Methods
    # --------------------------------------------------------------------------

    def _apply_filter(self, text: str):
        """Filter visible categories and blocks using the search text."""
        query = text.strip().lower()

        for i in range(self.tree.topLevelItemCount()):
            category_item = self.tree.topLevelItem(i)
            category_name = category_item.text(0)
            category_match = query in category_name.lower()  # ← startswith → in

            visible_children = 0
            for j in range(category_item.childCount()):
                block_item = category_item.child(j)
                block_name = block_item.text(0)
                block_match = query in block_name.lower()    # ← startswith → in
                visible = (not query) or category_match or block_match
                block_item.setHidden(not visible)
                if visible:
                    visible_children += 1

            category_visible = (not query) or category_match or (visible_children > 0)
            category_item.setHidden(not category_visible)
            category_item.setExpanded(bool(query and category_visible))
