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


class StateFeedBackMeta(BlockMeta):
    def __init__(self):
        self.name = "StateFeedback"
        self.category = "controllers"
        self.type = "state_feedback"
        self.summary = "Discrete-time state-feedback controller."
        self.description = (
            "Implements the static control law:\n"
            "$$\n"
            "u[k] = G r[k] - K x[k]\n"
            "$$\n"
        )

        self.parameters = [
            ParameterMeta(
                name="K",
                type="matrix",
                required=True,
                description="State feedback gain matrix."
            ),
            ParameterMeta(
                name="G",
                type="matrix",
                required=True,
                description="Reference feedforward gain matrix."
            ),
            ParameterMeta(
                name="sample_time",
                type="float",
                description="Block execution period."
            ),
        ]

        self.inputs = [
            PortMeta(
                name="r",
                display_as="r",
                shape=["p", 1]
            ),
            PortMeta(
                name="x",
                display_as="x",
                shape=["n", 1],
                description="State measurement vector."
            )
        ]

        self.outputs = [
            PortMeta(
                name="u",
                display_as="u",
                shape=["m", 1],
                description="Control input vector."
            ),
        ]
