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


class LuenbergerMeta(BlockMeta):

    def __init__(self):
        self.name = "Luenberger"
        self.category = "observers"
        self.type = "luenberger"
        self.summary = "Discrete-time Luenberger state observer."
        self.description = (
            "Implements the discrete-time observer equations:\n"
            "$$\n"
            "x̂[k+1] = A x̂[k] + B u[k] + L (y[k] - C x̂[k])\n"
            "$$\n"
            "$$\n"
            "ŷ[k] = C x̂[k]\n"
            "$$\n"
        )

        self.parameters = [
            ParameterMeta(
                name="A",
                type="matrix",
                required=True,
                description="System state matrix."
            ),
            ParameterMeta(
                name="B",
                type="matrix",
                required=True,
                description="Input matrix."
            ),
            ParameterMeta(
                name="C",
                type="matrix",
                required=True,
                description="Output matrix."
            ),
            ParameterMeta(
                name="L",
                type="matrix",
                required=True,
                description="Observer gain matrix."
            ),
            ParameterMeta(
                name="x0",
                type="vector",
                description="Initial estimated state."
            ),
            ParameterMeta(
                name="sample_time",
                type="float",
                description="Block execution period."
            ),
        ]

        self.inputs = [
            PortMeta(
                name="u",
                display_as="u",
                shape=["m", 1],
                description="Control input."
            ),
            PortMeta(
                name="y",
                display_as="y",
                shape=["p", 1],
                description="Measured output."
            ),
        ]

        self.outputs = [
            PortMeta(
                name="x_hat",
                display_as="x_hat",
                shape=["n", 1],
                description="Estimated state vector."
            ),
            PortMeta(
                name="y_hat",
                display_as="y_hat",
                shape=["p", 1],
                description="Estimated output."
            ),
        ]
