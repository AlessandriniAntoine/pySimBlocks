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

from typing import Literal, TYPE_CHECKING

from pySimBlocks.gui.blocks.port_meta import PortMeta

if TYPE_CHECKING:
    from pySimBlocks.gui.models.connection_instance import ConnectionInstance
    from pySimBlocks.gui.project_controller import BlockInstance

class PortInstance:
    """Represent a GUI port bound to a block instance.

    Attributes:
        name: Internal port name.
        display_as: Label shown in the GUI.
        direction: Port direction, either input or output.
        block: Owning block instance.
    """

    def __init__(
        self,
        name: str,
        display_as: str,
        direction: Literal['input', 'output'],
        block: "BlockInstance"
    ):
        """Initialize a port instance.

        Args:
            name: Internal port name.
            display_as: Label shown in the GUI.
            direction: Port direction.
            block: Owning block instance.

        Raises:
            None.
        """
        self.name = name
        self.display_as = display_as
        self.direction = direction
        self.block = block


    # --- Public methods ---

    def is_compatible(self, other: "PortInstance"):
        """Return whether this port can connect to another port.

        Args:
            other: Port to compare against.

        Returns:
            True if the ports have opposite directions.
        """
        return self.direction != other.direction

    def can_accept_connection(self, connections: list["ConnectionInstance"]) -> bool:
        """Return whether this port can accept one more connection.

        Args:
            connections: Existing connections currently attached to this port.

        Returns:
            True if the port can accept an additional connection.
        """
        return self.direction == "output" or not connections
