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
    clock: str = "internal" # "internal" or "external"

    def validate(self) -> None:
        """Verify that the configuration is valid.
        (ie: dt > 0, T > t0, solver is known)
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
    """
    Plot configuration.

    Describes how logged signals should be visualized.
    This object contains NO plotting logic.
    """

    plots: List[Dict[str, Any]]

    def validate(self) -> None:
        """Verify that the configuration is valid.
        (ie: each plot has required fields)
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
