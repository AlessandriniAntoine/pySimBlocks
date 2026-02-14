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


class DemuxMeta(BlockMeta):

    def __init__(self):
        self.name = "Demux"
        self.category = "operators"
        self.type = "demux"
        self.summary = "Vector split block (inverse of Mux)."
        self.description = (
            "Splits one input column vector into multiple output segments.\n"
            "For input length $n$ and $p$ outputs:\n"
            "$$\n"
            "q = n // p, \\quad m = n \\% p\n"
            "$$\n"
            "The first $m$ outputs have $(q+1)$ elements and the remaining\n"
            "$(p-m)$ outputs have $q$ elements.\n"
        )

        self.parameters = [
            ParameterMeta(
                name="num_outputs",
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
                display_as="in",
                shape=["n", 1],
                description="Input column vector to split."
            )
        ]

        self.outputs = [
            PortMeta(
                name="out",
                display_as="",
                shape=["k", 1],
                description="Output vector segments."
            )
        ]

    def resolve_port_group(
        self,
        port_meta: PortMeta,
        direction: Literal["input", "output"],
        instance: "BlockInstance"
    ) -> list["PortInstance"]:

        if direction == "output" and port_meta.name == "out":
            num_outputs = instance.parameters.get("num_outputs", 0)
            ports = []
            for i in range(1, num_outputs + 1):
                ports.append(
                    PortInstance(
                        name=f"{port_meta.name}{i}",
                        display_as=f"{i}",
                        direction="output",
                        block=instance
                    )
                )
            return ports

        return super().resolve_port_group(port_meta, direction, instance)
