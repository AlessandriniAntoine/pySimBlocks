from abc import ABC
from pathlib import Path
from typing import Any, Dict, List, Literal

from pySimBlocks.blocks_metadata.parameter_meta import ParameterMeta
from pySimBlocks.blocks_metadata.port_meta import PortMeta
from pySimBlocks.gui.model import BlockInstance, PortInstance


class BlockMeta(ABC):

    """
    Template for child class

from pySimBlocks.blocks_metadata.block_meta import BlockMeta
from pySimBlocks.blocks_metadata.parameter_meta import ParameterMeta
from pySimBlocks.blocks_metadata.port_meta import PortMeta

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