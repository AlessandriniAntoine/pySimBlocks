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
    """Time manager for fixed-step simulations.

    Handles multiple sample times by ensuring they are all integer multiples
    of the base time step.

    Attributes:
        dt: Base time step in seconds.
    """

    def __init__(self, dt_base: float, sample_times: list[float]):
        """Initialize the time manager.

        Args:
            dt_base: Base simulation time step in seconds.
            sample_times: List of block sample times to validate.

        Raises:
            ValueError: If dt_base is not strictly positive, or if any
                sample time is not an integer multiple of dt_base.
        """
        if dt_base <= 0:
            raise ValueError("Base time step must be strictly positive.")

        self.dt = dt_base
        self._check_sample_times(sample_times)

    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------

    def next_dt(self, t: float) -> float:
        """Return the next time step.

        Args:
            t: Current simulation time in seconds.

        Returns:
            The base time step dt (always fixed).
        """
        return self.dt

    # --------------------------------------------------------------------------
    # Private methods
    # --------------------------------------------------------------------------

    def _check_sample_times(self, sample_times: list[float]) -> None:
        """Raise if any sample time is not an integer multiple of dt."""
        eps = 1e-12
        for st in sample_times:
            ratio = st / self.dt
            if abs(ratio - round(ratio)) > eps:
                raise ValueError(
                    f"In fixed-step mode, sample_time={st} "
                    f"is not a multiple of base dt={self.dt}."
                )
