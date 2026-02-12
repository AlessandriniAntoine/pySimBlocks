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


class DeadZoneMeta(BlockMeta):

    def __init__(self):
        self.name = "DeadZone"
        self.category = "operators"
        self.type = "dead_zone"
        self.summary = "Discrete-time dead zone operator."
        self.description = (
            "Applies a dead-zone nonlinearity to the input signal:\n"
            "$$\n"
            "y = 0 \\quad \\text{if } \\text{lower\\_bound} \\le u \\le \\text{upper\\_bound}\n"
            "$$\n"
            "$$\n"
            "y = u - \\text{upper\\_bound} \\quad \\text{if } u > \\text{upper\\_bound}\n"
            "$$\n"
            "$$\n"
            "y = u - \\text{lower\\_bound} \\quad \\text{if } u < \\text{lower\\_bound}\n"
            "$$\n"
        )

        self.parameters = [
            ParameterMeta(
                name="lower_bound",
                type="scalar | vector | matrix",
                default=0.0
            ),
            ParameterMeta(
                name="upper_bound",
                type="scalar | vector | matrix",
                default=0.0
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
                shape=["n", "m"],
                description="Output signal after dead-zone operation."
            )
        ]
