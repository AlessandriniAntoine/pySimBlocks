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

class ProjectSimulationParams:

    DEFAULT_DT = 0.1
    DEFAULT_T = 10.
    DEFAULT_SOLVER = "fixed"
    DEFAULT_CLOCK = "internal"

    def __init__(
            self,
            dt: float = DEFAULT_DT,
            T: float = DEFAULT_T,
            solver: str = DEFAULT_SOLVER,
            clock: str = DEFAULT_CLOCK
    ):
        self.dt = dt
        self.T = T
        self.solver = solver
        self.clock = clock

    def load_from_dict(self, params: dict) -> None:
        self.dt = params.get("dt", self.dt)
        self.T = params.get("T", self.T)
        self.solver = params.get("solver", self.solver)
        self.clock = params.get("clock", self.clock)

    def clear(self) -> None:
        self.dt = self.DEFAULT_DT
        self.T = self.DEFAULT_T
        self.solver = self.DEFAULT_SOLVER
        self.clock = self.DEFAULT_CLOCK
