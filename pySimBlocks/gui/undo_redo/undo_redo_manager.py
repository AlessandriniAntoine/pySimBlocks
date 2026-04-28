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

from __future__ import annotations

from PySide6.QtGui import QAction, QUndoCommand, QUndoStack
from PySide6.QtWidgets import QWidget


class UndoManager:
    """Small facade around QUndoStack used by the GUI."""

    def __init__(self, undo_limit: int = 1000):
        self._stack = QUndoStack()
        self._stack.setUndoLimit(undo_limit)

    @property
    def stack(self) -> QUndoStack:
        return self._stack

    def push(self, command: QUndoCommand) -> None:
        self._stack.push(command)

    def clear(self) -> None:
        self._stack.clear()

    def undo(self) -> None:
        self._stack.undo()

    def redo(self) -> None:
        self._stack.redo()

    def set_clean(self) -> None:
        self._stack.setClean()

    def is_clean(self) -> bool:
        return self._stack.isClean()

    def create_undo_action(self, parent: QWidget) -> QAction:
        return self._stack.createUndoAction(parent, "Undo")

    def create_redo_action(self, parent: QWidget) -> QAction:
        return self._stack.createRedoAction(parent, "Redo")
