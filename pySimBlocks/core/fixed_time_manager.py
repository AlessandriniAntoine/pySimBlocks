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

class FixedStepTimeManager:
    """A time manager for fixed-step simulations.
    Handle multiple sample times by ensuring they are multiples of the base time step.
    """
    def __init__(self, dt_base: float, sample_times: list[float]):

        if dt_base <= 0:
            raise ValueError("Base time step must be strictly positive.")

        self.dt = dt_base
        self._check_sample_times(sample_times)

    def _check_sample_times(self, sample_times):
        """Ensure all sample times are multiples of the base time step."""
        eps = 1e-12
        for st in sample_times:
            ratio = st / self.dt
            if abs(ratio - round(ratio)) > eps:
                raise ValueError(
                    f"In fixed-step mode, sample_time={st} "
                    f"is not a multiple of base dt={self.dt}."
                )

    def next_dt(self, t):
        """Get the next time step (always fixed)."""
        return self.dt
