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

from typing import Literal
from pySimBlocks.gui.blocks.block_meta import BlockMeta
from pySimBlocks.gui.blocks.parameter_meta import ParameterMeta
from pySimBlocks.gui.blocks.port_meta import PortMeta
from pySimBlocks.gui.model import BlockInstance, PortInstance


class MuxMeta(BlockMeta):

    def __init__(self):
        self.name = "Mux"
        self.category = "operators"
        self.type = "mux"
        self.summary = "Vertical signal concatenation block."
        self.description = (
            "Concatenates multiple input column vectors vertically:\n"
            "$$\n"
            "\\mathrm{out} =\n"
            "\\begin{bmatrix}\n"
            "\\mathrm{in}_1 \\\\\n"
            "\\mathrm{in}_2 \\\\\n"
            "\\vdots \\\\\n"
            "\\mathrm{in}_N\n"
            "\\end{bmatrix}\n"
            "$$\n"
        )

        self.parameters = [
            ParameterMeta(
                name="num_inputs",
                type="int",
                autofill=True,
                default=2
            ),
            ParameterMeta(
                name="sample_time",
                type="float"
            )
        ]

        self.inputs = [
            PortMeta(
                name="in",
                display_as="",
                shape=["n", 1],
                description="Input column vectors to concatenate."
            )
        ]

        self.outputs = [
            PortMeta(
                name="out",
                display_as="out",
                shape=["m", 1],
                description="Vertically concatenated output vector."
            )
        ]

    def resolve_port_group(self, 
                           port_meta: PortMeta,
                           direction: Literal['input', 'output'], 
                           instance: "BlockInstance"
        ) -> list["PortInstance"]:

        if direction == "input" and port_meta.name == "in":
            num_inputs = instance.parameters.get("num_inputs", 0)
            ports = []
            for i in range(1, num_inputs + 1):
                ports.append(
                    PortInstance(
                        name=f"{port_meta.name}{i}",
                        display_as="",
                        direction="input",
                        block=instance
                    )
                )

            return ports

        return super().resolve_port_group(port_meta, direction, instance)
