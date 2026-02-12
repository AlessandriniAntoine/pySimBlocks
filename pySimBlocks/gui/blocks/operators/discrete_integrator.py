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


class DiscreteIntegratorMeta(BlockMeta):

    def __init__(self):
        self.name = "DiscreteIntegrator"
        self.category = "operators"
        self.type = "discrete_integrator"
        self.summary = "Discrete-time integrator block."
        self.description = (
            "Implements a discrete-time integration of the input signal.\n"
            "The state evolves according to:\n"
            "$$\n"
            "x[k+1] = x[k] + dt \\, u[k]\n"
            "$$\n"
            "with output:\n"
            "$$\n"
            "y[k] = x[k]\n"
            "$$\n"
            "for forward Euler integration."
        )

        self.parameters = [
            ParameterMeta(
                name="initial_state",
                type="scalar | vector | matrix"
            ),
            ParameterMeta(
                name="method",
                type="enum",
                autofill=True,
                default="euler forward",
                enum=["euler forward", "euler backward"]
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
                description="Input signal to integrate."
            )
        ]

        self.outputs = [
            PortMeta(
                name="out",
                display_as="out",
                shape=["n", "m"],
                description="Integrated output signal."
            )
        ]
