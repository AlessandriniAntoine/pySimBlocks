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


class GainMeta(BlockMeta):

    def __init__(self):
        self.name = "Gain"
        self.category = "operators"
        self.type = "gain"
        self.summary = "Static linear gain block."
        self.description = (
            "Computes:\n"
            "$$\n"
            "y = K \\cdot u\n"
            "$$\n"
        )

        self.parameters = [
            ParameterMeta(
                name="gain",
                type="scalar | vector | matrix",
                required=True,
                autofill=True,
                default=1.0,
                description="Gain coefficient."
            ),
            ParameterMeta(
                name="multiplication",
                type="enum",
                autofill=True,
                default="Element wise (K * u)",
                enum=["Element wise (K * u)", "Matrix (K @ u)", "Matrix (u @ K)"],
                description="Type of multiplication operation."
            ),
            ParameterMeta(
                name="sample_time",
                type="float"
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
                shape=["m", "m"],
                description="Output signal."
            )
        ]
