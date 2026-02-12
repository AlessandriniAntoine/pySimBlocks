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

import enum
from typing import Literal
from pySimBlocks.gui.blocks.block_meta import BlockMeta
from pySimBlocks.gui.blocks.parameter_meta import ParameterMeta
from pySimBlocks.gui.blocks.port_meta import PortMeta
from pySimBlocks.gui.model import BlockInstance, PortInstance


class ProductMeta(BlockMeta):

    def __init__(self):
        self.name = "Product"
        self.category = "operators"
        self.type = "product"
        self.summary = "Multi-input product block."
        self.description = (
            "If \"Element-wise (*)\" is selected, this block computes the element-wise:\n"
            "$$\n"
            "y = u_1 operations_1 u_2 operations_2 ... operations_m-1 u_m\n"
            "$$\n"
            "where u_i are the input signals and operations_i are the operations selected * or /.\n\n"
            "If \"Matrix (@)\" is selected, this block computes the matrix product:\n"
            "$$\n"
            "y = u_1 operations_1 u_2 operations_2 ... operations_m-1 u_m\n"
            "$$\n"
            "where u_i are the input signals and operations_i are the operations selected * (@) or / (inverse)."
        )

        self.parameters = [
            ParameterMeta(
                name="operations",
                type="str",
                autofill=True,
                default="*"
            ),
            ParameterMeta(
                name="multiplication",
                type="enum",
                autofill=True,
                default="Element-wise (*)",
                enum=["Element-wise (*)", "Matrix (@)"]
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
                shape=["n", "m"],
                description="Input signals."
            )
        ]

        self.outputs = [
            PortMeta(
                name="out",
                display_as="out",
                shape=["n", "m"],
                description="Output signal."
            )
        ]

    def resolve_port_group(
        self,
        port_meta: PortMeta,
        direction: Literal['input', 'output'],
        instance: "BlockInstance"
    ) -> list["PortInstance"]:

        if direction == port_meta.name == "input":
            operations_str = instance.parameters.get("operations", "")
            ports = []
            for i, op in enumerate(operations_str):
                ports.append(
                    PortInstance(
                        name=f"{port_meta.name}_{i}",
                        display_as=op,
                        direction="input",
                        block=instance
                    )
                )

            return ports

        return super().resolve_port_group(port_meta, direction, instance)
