# ******************************************************************************
#                                  pySimBlocks
#                     Copyright (c) 2026 Université de Lille & INRIA
# ******************************************************************************

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QWidget,
)


class ViewNavigationBar(QWidget):
    """Breadcrumb bar for diagram / group view navigation."""

    navigate_requested = Signal(int)

    ROOT_LABEL = "Diagram"

    def __init__(
        self,
        resolve_group_name: Callable[[str], str | None],
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._resolve_group_name = resolve_group_name
        self._view_stack: list[str] = []

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(6, 4, 6, 4)
        self._layout.setSpacing(4)
        self._layout.addStretch(1)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def set_view_stack(self, stack_uids: list[str]) -> None:
        """Rebuild breadcrumb buttons from the current view stack."""
        self._view_stack = list(stack_uids)

        while self._layout.count():
            item = self._layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self._add_segment_button(self.ROOT_LABEL, depth=0, enabled=len(stack_uids) > 0)

        for depth, group_uid in enumerate(stack_uids, start=1):
            self._layout.addWidget(self._separator())
            name = self._resolve_group_name(group_uid) or "Group"
            is_current = depth == len(stack_uids)
            self._add_segment_button(name, depth=depth, enabled=not is_current)

        self._layout.addStretch(1)

    def _separator(self) -> QLabel:
        label = QLabel("›", self)
        font = QFont(label.font())
        if font.pointSize() > 0:
            font.setPointSize(font.pointSize() + 2)
        font.setBold(True)
        label.setFont(font)
        label.setStyleSheet("color: palette(windowText); padding: 0 4px;")
        label.setAlignment(Qt.AlignCenter)
        return label

    def _add_segment_button(self, text: str, depth: int, enabled: bool) -> None:
        button = QPushButton(text, self)
        button.setFlat(True)
        button.setCursor(Qt.PointingHandCursor if enabled else Qt.ArrowCursor)
        button.setEnabled(enabled)
        if not enabled:
            font = button.font()
            font.setBold(True)
            button.setFont(font)
        if enabled:
            button.clicked.connect(lambda _checked=False, d=depth: self.navigate_requested.emit(d))
        self._layout.addWidget(button)
