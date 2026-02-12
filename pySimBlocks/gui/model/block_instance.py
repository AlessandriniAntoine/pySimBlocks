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

import uuid
from typing import TYPE_CHECKING, Any, Dict, List

from pySimBlocks.gui.model.port_instance import PortInstance

try: # Python 3.11+
    from typing import Self
except ImportError: # Python <3.11
    from typing_extensions import Self


if TYPE_CHECKING:
    from pySimBlocks.gui.blocks.block_meta import BlockMeta


class BlockInstance:
    """
    GUI-side mutable instance of a block.

    - References an immutable BlockMeta
    - Stores instance-level data (name, parameters)
    - Used by BlockItem and BlockDialog
    """

    @classmethod
    def copy(cls, block: Self) -> Self:
        cpy = BlockInstance(block.meta)
        cpy.name = block.name
        cpy.parameters = block.parameters.copy()
        return cpy


    def __init__(self, meta: 'BlockMeta'):
        self.uid: str = uuid.uuid4().hex
        self.meta = meta
        self.name: str = meta.name
        self.parameters: Dict[str, Any] = self._init_parameters()
        self.ports: List[PortInstance] = []

    def _init_parameters(self) -> dict[str, Any]:
        """
        Initialize instance parameters from metadata.
        """
        params = {}

        for p in self.meta.parameters:
            params[p.name] = p.default if p.autofill else None

        return params

    def update_params(self, params: dict[str, Any]):
        for k, v in params.items():
            if k in self.parameters:
                self.parameters[k] = v

    def resolve_ports(self) -> None:
        self.ports = self.meta.build_ports(self)

    def active_parameters(self):
        return  {
            k: v
            for k, v in self.parameters.items()
            if self.meta.is_parameter_active(k, self.parameters)
        }
    
    """
        ports: List[PortInstance] = []

        for direction in ("input", "output"):
            for pmeta in self.meta.ports[f"{direction}s"]:
                ports.extend(self._resolve_port_group(pmeta, direction))
        self.ports = ports

    def _resolve_port_group(self, pmeta: Dict[str, Dict[str, Any]], direction: Literal['input', 'output']) -> list[PortInstance]:
        if not pmeta["dynamic"]:
            return [PortInstance(pmeta["pattern"], direction, self, pmeta)]

        source = pmeta["source"]
        pattern = pmeta["pattern"]

        if source["type"] == "parameter":
            value = self.parameters.get(source["parameter"])

            if value is None and "fallback" in pmeta:
                value = self.parameters.get(
                    pmeta["fallback"]["parameter"],
                    pmeta["fallback"]["default"],
                )
            return self._expand_ports(pattern, value, direction, pmeta)

        return []

    def _expand_ports(self,
            pattern: str,
            value: Sized,
            direction: Literal['input', 'output'],
            meta: Dict[str, Dict[str, str]]
    ) -> list[PortInstance]:

        ports: List[PortInstance] = []
        operation: str = meta["source"].get("operation", "")

        if operation == "len":
            for i in range(1, len(value) + 1):
                ports.append(PortInstance(pattern.format(val=i), direction, self, meta))

        elif operation == "len + 1":
            for i in range(1, len(value) + 2):
                ports.append(PortInstance(pattern.format(val=i), direction, self, meta))

        elif operation == "keys":
            if value:
                for key in value:
                    ports.append(
                        PortInstance(pattern.format(val=key), direction, self, meta)
                    )

        elif operation == "value":
            for i in range(1, int(value) + 1):
                ports.append(PortInstance(pattern.format(val=i), direction, self, meta))

        return ports
        """
