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


class StepMeta(BlockMeta):

    def __init__(self):
        self.name = "Step"
        self.category = "sources"
        self.type = "step"
        self.summary = "Step signal source."
        self.description = (
            "Generates a step signal defined by:\n"
            "$$\n"
            "y(t) =\n"
            "\\begin{cases}\n"
            "y_{\\text{before}}, & t < t_0 \\\\\n"
            "y_{\\text{after}},  & t \\geq t_0\n"
            "\\end{cases}\n"
            "$$\n"
        )

        self.parameters = [
            ParameterMeta(
                name="value_before",
                type="scalar | vector | matrix",
                required=True,
                autofill=True,
                default=[[0.0]],
                description="Output value before the step time."
            ),
            ParameterMeta(
                name="value_after",
                type="scalar | vector | matrix",
                required=True,
                autofill=True,
                default=[[1.0]],
                description="Output value after the step time."
            ),
            ParameterMeta(
                name="start_time",
                type="float",
                required=True,
                autofill=True,
                default=1.0,
                description="Time at which the step occurs."
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
                description="Step output signal."
            )
        ]
