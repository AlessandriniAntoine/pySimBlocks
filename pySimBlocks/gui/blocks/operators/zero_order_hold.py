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


class ZeroOrderHoldMeta(BlockMeta):

    def __init__(self):
        self.name = "ZeroOrderHold"
        self.category = "operators"
        self.type = "zero_order_hold"
        self.summary = "Zero-Order Hold (ZOH) block."
        self.description = (
            "Samples the input signal at discrete instants and holds its value\n"
            "constant between sampling instants. The held output is updated when\n"
            "the elapsed time since the last sampling instant reaches the sampling\n"
            "period."
        )

        self.parameters = [
            ParameterMeta(
                name="sample_time",
                type="float",
                required=True
            )
        ]

        self.inputs = [
            PortMeta(
                name="in",
                display_as="in",
                shape=["n", "m"],
                description="Input signal."
            )
        ]

        self.outputs = [
            PortMeta(
                name="out",
                display_as="out",
                shape=["n", "m"],
                description="Held output signal."
            )
        ]
