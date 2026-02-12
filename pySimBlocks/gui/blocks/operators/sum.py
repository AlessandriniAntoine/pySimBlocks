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
from pySimBlocks.gui.blocks.block_meta import BlockMeta, ParameterMeta
from pySimBlocks.gui.blocks.port_meta import PortMeta
from pySimBlocks.gui.model import BlockInstance, PortInstance

class SumMeta(BlockMeta):

    def __init__(self):
        self.name = "Sum"
        self.category = "operators"
        self.type = "sum"
        self.summary = "Multi-input summation block."
        self.description = (
            "Computes:\n"
            "$$\n"
            r"y = \sum_i s_i \cdot u_i""\n"
            "$$\n"
        )

        self.parameters = [
            ParameterMeta(
                name="signs",
                type="str",
                autofill=True,
                default="++"
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
                shape=["n", "m"]
            ),
        ]

        self.outputs = [
            PortMeta(
                name="out",
                display_as="out",
                shape=["n", "m"]
            ),
        ]
    
    def resolve_port_group(self, 
                           port_meta: PortMeta,
                           direction: Literal['input', 'output'], 
                           instance: "BlockInstance"
        ) -> list["PortInstance"]:

        if direction == "input" and port_meta.name == "in":
            signs = instance.parameters.get("signs", "")
            ports = []

            for i, sign in enumerate(signs):
                ports.append(
                    PortInstance(
                        name=f"{port_meta.name}{i + 1}",
                        display_as=sign,
                        direction="input",
                        block=instance
                    )
                )
            return ports
        
        return super().resolve_port_group(port_meta, direction, instance)
