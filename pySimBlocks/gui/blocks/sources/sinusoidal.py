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


class SinusoidalMeta(BlockMeta):

    def __init__(self):
        self.name = "Sinusoidal"
        self.category = "sources"
        self.type = "sinusoidal"
        self.summary = "Multi-dimensional sinusoidal signal source."
        self.description = (
            "Generates a sinusoidal signal defined by:\n"
            "$$\n"
            "y_i(t) = A_i \\sin(2\\pi f_i t + \\varphi_i) + o_i\n"
            "$$\n"
        )

        self.parameters = [
            ParameterMeta(
                name="amplitude",
                type="scalar | vector | matrix",
                required=True,
                autofill=True,
                default=[[1.0]],
                description="Sinusoidal amplitude."
            ),
            ParameterMeta(
                name="frequency",
                type="scalar | vector | matrix",
                required=True,
                autofill=True,
                default=[[1.0]],
                description="Sinusoidal frequency in Hertz."
            ),
            ParameterMeta(
                name="phase",
                type="scalar | vector | matrix",
                description="Phase shift in radians."
            ),
            ParameterMeta(
                name="offset",
                type="scalar | vector | matrix",
                description="Constant offset added to the signal."
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
                description="Sinusoidal output signal."
            )
        ]
