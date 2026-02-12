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

from abc import ABC
from pathlib import Path
from typing import Any, Dict, List, Literal

from pySimBlocks.gui.blocks.parameter_meta import ParameterMeta
from pySimBlocks.gui.blocks.port_meta import PortMeta
from pySimBlocks.gui.model import BlockInstance, PortInstance


class BlockMeta(ABC):

    """
    Template for child class

from pySimBlocks.gui.blocks.block_meta import BlockMeta
from pySimBlocks.gui.blocks.parameter_meta import ParameterMeta
from pySimBlocks.gui.blocks.port_meta import PortMeta

class MyBlockMeta(BlockMeta):

    def __init__(self):
        self.name = ""
        self.category = ""
        self.type = ""
        self.summary = ""
        self.description = (
            ""
        )

        self.parameters = [
            ParameterMeta(
                name="",
                type=""
            ),
        ]

        self.inputs = [
            PortMeta(
                name="",
                display_as=""
                shape=...
            ),
        ]

        self.outputs = [
            PortMeta(
                name="",
                display_as=""
                shape=...
            ),
        ]
    """


    # ----------- Mandatory class attributes (must be overridden) -----------
    name: str
    category: str
    type: str
    summary: str
    description: str

    # ----------- Optional declarations -----------

    doc_path: Path | None = None
    parameters: List[ParameterMeta] = []
    inputs: List[PortMeta] = []
    outputs: List[PortMeta] = []

    def get_param(self, param_name: str) -> ParameterMeta | None:
        for param in self.parameters:
            if param.name == param_name:
                return param
        return None

    def is_parameter_active(self, param_name: str, instance_values: Dict[str, Any]) -> bool:
        """
        Default: all parameters are always active.
        Children override if needed.
        """
        return True
    
    def resolve_port_group(self, 
                           port_meta: PortMeta,
                           direction: Literal['input', 'output'], 
                           instance: "BlockInstance"
    ) -> list["PortInstance"]:
        """
        Default behavior: fixed port.
        Children override for dynamic ports.
        """
        return [PortInstance(port_meta.name, port_meta.display_as, direction, instance)]
    
    def build_ports(self, instance: "BlockInstance") -> list["PortInstance"]:
        ports = []

        for pmeta in self.inputs:
            ports.extend(self.resolve_port_group(pmeta, "input", instance))

        for pmeta in self.outputs:
            ports.extend(self.resolve_port_group(pmeta, "output", instance))

        return ports
