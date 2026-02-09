from abc import ABC
from typing import Any, Dict, List

from pySimBlocks.blocks_metadata.block_parameter import ParameterMeta
from pySimBlocks.blocks_metadata.port_meta import PortMeta
from pySimBlocks.gui.model import BlockInstance, PortInstance


class BlockMeta(ABC):

    # ----------- Mandatory class attributes (must be overridden) -----------
    name: str
    category: str
    type: str
    summary: str
    description: str

    # ----------- Optional declarations -----------

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
                           direction: str, 
                           instance: "BlockInstance"
    ) -> list["PortInstance"]:
        """
        Default behavior: fixed port.
        Children override for dynamic ports.
        """
        return [PortInstance(port_meta.display_as, direction, instance, port_meta)]
    
    def build_ports(self, instance: "BlockInstance") -> list["PortInstance"]:
        """
        Default port resolution.
        """
        ports = []

        for pmeta in self.inputs:
            ports.extend(self.resolve_port_group(pmeta, "input", instance))

        for pmeta in self.outputs:
            ports.extend(self.resolve_port_group(pmeta, "output", instance))

        return ports