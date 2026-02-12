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


class RampMeta(BlockMeta):

    def __init__(self):
        self.name = "Ramp"
        self.category = "sources"
        self.type = "ramp"
        self.summary = "Multi-dimensional ramp signal source."
        self.description = (
            "Generates a ramp signal defined by:\n"
            "$$\n"
            "y_i(t) = o_i + s_i \\max(0, t - t_{0,i})\n"
            "$$\n"
        )

        self.parameters = [
            ParameterMeta(
                name="slope",
                type="scalar | vector | matrix",
                required=True,
                autofill=True,
                default=[[1.0]],
                description="Ramp slope for each output dimension."
            ),
            ParameterMeta(
                name="start_time",
                type="scalar | vector | matrix",
                description="Time at which the ramp starts."
            ),
            ParameterMeta(
                name="offset",
                type="scalar | vector | matrix",
                description="Output value before the ramp starts."
            ),
            ParameterMeta(
                name="sample_time",
                type="float",
                description="Block execution period."
            )
        ]

        self.outputs = [
            PortMeta(
                name="out",
                display_as="out",
                shape=["n", "m"],
                description="Ramp output signal."
            )
        ]
