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

from typing import Any, Dict, Literal, TYPE_CHECKING

if TYPE_CHECKING:
    from pySimBlocks.gui.model.connection_instance import ConnectionInstance
    from pySimBlocks.gui.project_controller import BlockInstance

class PortInstance:
    def __init__(
        self,
        name: str,
        direction: Literal['input', 'output'],
        block: "BlockInstance",
        meta: Dict[str, Any],
    ):
        self.name = name
        self.direction = direction
        self.block = block
        self.meta = meta

    def is_compatible(self, other: "PortInstance"):
        return self.direction != other.direction
    
    def can_accept_connection(self, connections: list["ConnectionInstance"]) -> bool:
        """
        Check whether this port can accept a new connection.

        The `connections` list is expected to contain all and only the connections
        already linked to this PortInstance.
        """
        return self.direction == "output" or not connections

