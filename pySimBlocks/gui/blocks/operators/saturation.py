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


class SaturationMeta(BlockMeta):

    def __init__(self):
        self.name = "Saturation"
        self.category = "operators"
        self.type = "saturation"
        self.summary = "Discrete-time saturation operator."
        self.description = (
            "Applies element-wise saturation to the input signal:\n"
            "$$\n"
            "y[k] = \\mathrm{clip}(u[k], u_{\\min}, u_{\\max})\n"
            "$$\n"
            "where $u_{\\min}$ and $u_{\\max}$ define the lower and upper bounds."
        )

        self.parameters = [
            ParameterMeta(
                name="u_min",
                type="scalar | vector | matrix"
            ),
            ParameterMeta(
                name="u_max",
                type="scalar | vector | matrix"
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
                shape=["n", 1],
                description="Input signal."
            )
        ]

        self.outputs = [
            PortMeta(
                name="out",
                display_as="out",
                shape=["n", "m"],
                description="Saturated output signal."
            )
        ]
