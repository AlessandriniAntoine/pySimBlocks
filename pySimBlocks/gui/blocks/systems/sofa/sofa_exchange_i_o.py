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


class SofaExchangeIOMeta(BlockMeta):

    def __init__(self):
        self.name = "SofaExchangeIO"
        self.category = "systems"
        self.type = "sofa_exchange_i_o"
        self.summary = "Interface block for exchanging signals between pySimBlocks and SOFA."
        self.description = (
            "Provides a stateless interface block that exposes dynamic input and output\n"
            "ports to connect a pySimBlocks model with an external SOFA controller.\n"
            "This block does not execute a SOFA simulation."
        )

        self.parameters = [
            ParameterMeta(
                name="scene_file",
                type="string",
                description="Path to the SOFA scene file used for automatic generation relative to parameters.yaml file."
            ),
            ParameterMeta(
                name="input_keys",
                type="list[string]",
                required=True,
                description="List of input keys corresponding to SOFA input ports."
            ),
            ParameterMeta(
                name="output_keys",
                type="list[string]",
                required=True,
                description="List of output keys corresponding to SOFA output ports."
            ),
            ParameterMeta(
                name="slider_params",
                type="dict",
                description="Dictionary of slider parameters to be modified in the SOFA scene at runtime."
            ),
            ParameterMeta(
                name="sample_time",
                type="float"
            )
        ]

        self.inputs = [
            PortMeta(
                name="sofa_inputs",
                display_as="",
                shape=[]
            )
        ]

        self.outputs = [
            PortMeta(
                name="sofa_outputs",
                display_as="",
                shape=[]
            )
        ]

    def resolve_port_group(
        self,
        port_meta: PortMeta,
        direction: Literal["input", "output"],
        instance: "BlockInstance"
    ) -> list["PortInstance"]:

        if direction == "input" and port_meta.name == "sofa_inputs":
            keys = instance.parameters.get("input_keys", [])
            if keys is None:
                return []
            return [
                PortInstance(
                    name=key,
                    display_as=key,
                    direction="input",
                    block=instance
                )
                for key in keys
            ]

        if direction == "output" and port_meta.name == "sofa_outputs":
            keys = instance.parameters.get("output_keys", [])
            if keys is None:
                return []
            return [
                PortInstance(
                    name=key,
                    display_as=key,
                    direction="output",
                    block=instance
                )
                for key in keys
            ]

        return super().resolve_port_group(port_meta, direction, instance)
