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

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pySimBlocks.gui.graphics.port_item import PortInstance
    from pySimBlocks.gui.project_controller import BlockInstance

class ConnectionInstance:
    """Represent a connection between two GUI ports.

    Attributes:
        src_port: Source port of the connection.
        dst_port: Destination port of the connection.
    """

    def __init__(
        self,
        src_port: "PortInstance",
        dst_port: "PortInstance",
    ):
        """Initialize a connection instance.

        Args:
            src_port: Source port of the connection.
            dst_port: Destination port of the connection.

        Raises:
            None.
        """
        self.src_port = src_port
        self.dst_port = dst_port


    # --- Public methods ---

    def src_block(self) -> "BlockInstance":
        """Return the source block of the connection.

        Returns:
            Block owning the source port.
        """
        return self.src_port.block

    def dst_block(self) -> "BlockInstance":
        """Return the destination block of the connection.

        Returns:
            Block owning the destination port.
        """
        return self.dst_port.block

    def is_block_involved(self, block: "BlockInstance") -> bool:
        """Return whether the given block participates in the connection.

        Args:
            block: Block instance to test.

        Returns:
            True if the block owns either connection endpoint.
        """
        return block in (self.src_port.block, self.dst_port.block)
