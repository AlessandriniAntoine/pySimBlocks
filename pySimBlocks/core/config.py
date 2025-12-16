from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

# ---------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------
@dataclass(frozen=True)
class SimulationConfig:
    """
    Simulation execution configuration.

    This object contains ONLY execution-related parameters.
    It must not contain any model or block-specific information.
    """

    dt: float
    T: float
    t0: float = 0.0
    solver: str = "fixed"
    logging: List[str] = field(default_factory=list)

    def validate(self) -> None:
        if self.dt <= 0.0:
            raise ValueError("SimulationConfig.dt must be > 0")

        if self.T <= self.t0:
            raise ValueError("SimulationConfig.T must be > t0")

        if self.solver not in {"fixed", "variable"}:
            raise ValueError(
                f"Unknown solver '{self.solver}'. "
                "Allowed values: {'fixed', 'variable'}"
            )


@dataclass
class ModelConfig:
    """
    Model numerical parameters configuration.

    Stores parameters for each block, indexed by block name.
    No structural information is allowed here.
    """

    blocks: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def has_block(self, name: str) -> bool:
        return name in self.blocks

    def get_block_params(self, name: str) -> Dict[str, Any]:
        if name not in self.blocks:
            raise KeyError(f"No parameters defined for block '{name}'")
        return self.blocks[name]

    def validate(self, block_names: Optional[List[str]] = None) -> None:
        """
        Optional validation against a list of model block names.
        """
        if block_names is None:
            return

        unknown = set(self.blocks.keys()) - set(block_names)
        if unknown:
            raise ValueError(
                f"Parameters defined for unknown blocks: {sorted(unknown)}"
            )
