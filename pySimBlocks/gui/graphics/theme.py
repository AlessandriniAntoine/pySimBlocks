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

from dataclasses import dataclass

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication


def _luma(c: QColor) -> float:
    r, g, b, _ = c.getRgb()
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _ensure_contrast(fg: QColor, bg: QColor, min_delta: float = 80.0) -> QColor:
    """Ensure |luma(fg) - luma(bg)| >= min_delta by pushing fg to black/white."""
    if abs(_luma(fg) - _luma(bg)) >= min_delta:
        return fg

    # push toward white on dark bg, toward black on light bg
    if _luma(bg) < 128:
        return QColor(235, 235, 235)
    return QColor(25, 25, 25)


def _separate_bg(block: QColor, scene: QColor, delta: float = 35.0) -> QColor:
    """Make sure block background is separated from scene background."""
    if abs(_luma(block) - _luma(scene)) >= delta:
        return block

    # If scene is dark -> lighten block a bit; if scene is light -> darken block a bit
    h, s, l, a = block.getHsl()
    if _luma(scene) < 128:
        l = min(255, l + 30)
    else:
        l = max(0, l - 30)
    out = QColor()
    out.setHsl(h, s, l, a)
    return out


@dataclass(frozen=True)
class Theme:
    scene_bg: QColor

    block_bg: QColor
    block_bg_selected: QColor
    block_border: QColor
    block_border_selected: QColor

    text: QColor
    text_selected: QColor

    wire: QColor

    port_in: QColor
    port_out: QColor


def make_theme() -> Theme:
    pal = QApplication.palette()

    scene_bg = pal.color(QPalette.Window)
    is_dark = _luma(scene_bg) < 128

    # base colors
    if is_dark:
        block_bg = QColor("#30343A")    
        block_bg_selected = QColor("#3A6FB0")
        block_border = QColor("#C9C956")
        block_border_selected = QColor("#6FAEFF")
    else:
        block_bg = QColor("#ECECEC")    
        block_bg_selected = QColor("#C7DBFF")
        block_border = QColor("#6E6E6E")
        block_border_selected = QColor("#4A78FF")

    text = QColor("#F0F0F0") if is_dark else QColor("#1E1E1E")
    text_selected = QColor("#FFFFFF") if is_dark else QColor("#000000")
    wire = QColor("#E6E6E6") if is_dark else QColor("#1A1A1A")

    text = _ensure_contrast(text, block_bg, min_delta=90.0)
    text_selected = _ensure_contrast(text_selected, block_bg_selected, min_delta=90.0)
    block_border = _ensure_contrast(block_border, block_bg, min_delta=60.0)
    block_border_selected = _ensure_contrast(block_border_selected, block_bg_selected, min_delta=60.0)
    wire = _ensure_contrast(wire, scene_bg, min_delta=110.0)

    port_in = QColor("#5FBF73")
    port_out = QColor("#E5534B")

    return Theme(
        scene_bg=scene_bg,
        block_bg=block_bg,
        block_bg_selected=block_bg_selected,
        block_border=block_border,
        block_border_selected=block_border_selected,
        text=text,
        text_selected=text_selected,
        wire=wire,
        port_in=port_in,
        port_out=port_out,
    )
