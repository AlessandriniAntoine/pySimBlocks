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

from dataclasses import dataclass, field
from typing import Any, Dict, List


# ---------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------
@dataclass(frozen=True)
class SimulationConfig:
    """Simulation execution configuration.
 
    Contains only execution-related parameters. Must not hold any
    model or block-specific information.
    """
    
    #: Simulation time step in seconds.
    dt: float
    
    #: Simulation end time in seconds.
    T: float
    
    #: Simulation start time in seconds.
    t0: float = 0.0
    
    #: Integration scheme, either ``"fixed"`` or ``"variable"``.
    solver: str = "fixed"
    
    #: Signals to log during simulation.
    logging: List[str] = field(default_factory=list)
    
    #: Clock source, either ``"internal"`` or ``"external"``.
    clock: str = "internal" 

    def validate(self) -> None:
        """Verify that the configuration is consistent.
 
        Checks that dt > 0, T > t0, solver and clock are known values.
 
        Raises:
            ValueError: If any parameter is invalid or out of range.
        """
        if self.dt <= 0.0:
            raise ValueError("SimulationConfig.dt must be > 0")

        if self.T <= self.t0:
            raise ValueError("SimulationConfig.T must be > t0")

        if self.solver not in {"fixed", "variable"}:
            raise ValueError(
                f"Unknown solver '{self.solver}'. "
                "Allowed values: {'fixed', 'variable'}"
            )

        if self.clock not in {"internal", "external"}:
            raise ValueError(
                f"Unknown clock '{self.clock}'. "
                "Allowed values: {'internal', 'external'}"
            )


@dataclass
class PlotConfig:
    """Plot configuration.
 
    Describes how logged signals should be visualized.
    Contains no plotting logic.
 
    Attributes:
        plots: List of plot descriptors. Each descriptor is a dict that
            must contain at least a ``"signals"`` key with a list of
            signal names.
    """

    plots: List[Dict[str, Any]]

    def validate(self) -> None:
        """Verify that each plot descriptor has the required fields.
 
        Raises:
            ValueError: If a plot descriptor is missing ``"signals"`` or
                if ``"signals"`` is not a list.
        """
        for i, plot in enumerate(self.plots):
            if "signals" not in plot:
                raise ValueError(
                    f"Plot #{i} is missing required field 'signals'"
                )
            if not isinstance(plot["signals"], list):
                raise ValueError(
                    f"'signals' in plot #{i} must be a list"
                )
