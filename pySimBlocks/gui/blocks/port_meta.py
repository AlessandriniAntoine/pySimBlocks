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


from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PortMeta:
    """Describe one declared input or output port of a GUI block.

    Attributes:
        name: Internal port name.
        display_as: User-facing port label.
        shape: Symbolic shape description shown in metadata.
        description: Optional help text displayed in the GUI.
    """
    name: str
    display_as: str
    shape: list[Any]
    description: str = ""
