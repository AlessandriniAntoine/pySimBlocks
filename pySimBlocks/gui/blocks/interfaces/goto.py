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

from pySimBlocks.gui.blocks.block_meta import BlockMeta
from pySimBlocks.gui.blocks.parameter_meta import ParameterMeta
from pySimBlocks.gui.blocks.port_meta import PortMeta


class GotoMeta(BlockMeta):
    """Describe the GUI metadata of the Goto interface block."""

    def __init__(self):
        """Initialize Goto block metadata.

        Args:
            None.

        Raises:
            None.
        """
        self.name = "Goto"
        self.category = "interfaces"
        self.type = "goto"
        self.summary = "Publish a signal to the virtual signal bus."
        self.description = (
            "Writes the input signal to the global signal bus under a named **tag**.\n\n"
            "Any **From** block in the same diagram that shares the same tag will\n"
            "automatically receive this value each tick, without requiring an explicit\n"
            "wire connection.\n\n"
            "The topological sort guarantees that this block executes before all\n"
            "matching From blocks within the same simulation step."
        )

        self.parameters = [
            ParameterMeta(
                name="tag",
                type="str",
                required=True,
                description=(
                    "Signal bus tag. Must match the tag of the corresponding "
                    "From block(s)."
                ),
            ),
            ParameterMeta(
                name="sample_time",
                type="float",
            ),
        ]

        self.inputs = [
            PortMeta(
                name="in",
                display_as="in",
                shape=["n", 1],
                description="Signal to publish on the bus.",
            )
        ]
