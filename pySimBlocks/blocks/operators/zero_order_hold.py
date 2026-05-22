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

from __future__ import annotations

import numpy as np

from pySimBlocks.core.block import Block


class ZeroOrderHold(Block):
    """Zero-Order Hold (ZOH) block.

    Samples the input at discrete instants separated by ``sample_time`` and
    holds the sampled value constant between sampling instants. The input shape
    is frozen after the first resolution.

    Attributes:
        sample_time: Sampling period in seconds.
    """

    direct_feedthrough = True

    def __init__(self, name: str, sample_time: float):
        """Initialize a ZeroOrderHold block.

        Args:
            name: Unique identifier for this block instance.
            sample_time: Sampling period Ts (> 0) in seconds.

        Raises:
            ValueError: If ``sample_time`` is not a positive number.
        """
        super().__init__(name, sample_time)

        if not isinstance(sample_time, (float, int)) or float(sample_time) <= 0.0:
            raise ValueError(f"[{self.name}] sample_time must be > 0.")

        self.sample_time = float(sample_time)
        self.EPS = 1e-12

        self.set_input("in", None)
        self.set_output("out", None)

        self.set_state("y", None)
        self.set_next_state("y", None)
        self.set_state("t_last", None)
        self.set_next_state("t_last", None)

        self._resolved_shape: tuple[int, int] | None = None


    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------

    def initialize(self, t0: float) -> None:
        """Sample the initial input and set up the hold state.

        Args:
            t0: Initial simulation time in seconds.

        Raises:
            RuntimeError: If input ``'in'`` is None at initialization.
            ValueError: If input is not 2D.
        """
        u = self.get_input("in")
        if u is None:
            raise RuntimeError(f"[{self.name}] Input 'in' is None at initialization.")

        u = self._to_2d_array("input", u)
        self._ensure_shape(u)

        y0 = u.copy()
        self.set_state("y", y0)
        self.set_state("t_last", float(t0))

        self.set_next_state("y", y0.copy())
        self.set_next_state("t_last", float(t0))

        self.set_output("out", y0.copy())

    def output_update(self, t: float, dt: float) -> None:
        """Output the current sample or the held value depending on the elapsed time.

        Args:
            t: Current simulation time in seconds.
            dt: Current time step in seconds.

        Raises:
            RuntimeError: If input ``'in'`` is None or block is not initialized.
        """
        u = self.get_input("in")
        if u is None:
            raise RuntimeError(f"[{self.name}] Input 'in' is None.")

        u = self._to_2d_array("input", u)
        self._ensure_shape(u)

        t_last = self.get_state("t_last")
        if t_last is None:
            raise RuntimeError(f"[{self.name}] ZOH not initialized (t_last is None).")

        if (t - t_last) >= self.sample_time - self.EPS:
            self.set_output("out", u.copy())
        else:
            self.set_output("out", self.get_state("y").copy())

    def state_update(self, t: float, dt: float) -> None:
        """Update the held value and timestamp if a new sample was taken.

        Args:
            t: Current simulation time in seconds.
            dt: Current time step in seconds.

        Raises:
            RuntimeError: If block is not initialized.
        """
        t_last = self.get_state("t_last")
        if t_last is None:
            raise RuntimeError(f"[{self.name}] ZOH not initialized (t_last is None).")

        if (t - t_last) >= self.sample_time - self.EPS:
            self.set_next_state("y", self.get_output("out").copy())
            self.set_next_state("t_last", float(t))
        else:
            self.set_next_state("y", self.get_state("y").copy())
            self.set_next_state("t_last", float(t_last))


    # --------------------------------------------------------------------------
    # Private methods
    # --------------------------------------------------------------------------

    def _ensure_shape(self, u: np.ndarray) -> None:
        """Validate input shape and freeze it on the first call."""
        if u.ndim != 2:
            raise ValueError(
                f"[{self.name}] Input 'in' must be a 2D array. Got ndim={u.ndim} with shape {u.shape}."
            )
        if self._resolved_shape is None:
            self._resolved_shape = u.shape
            return
        if u.shape != self._resolved_shape:
            raise ValueError(
                f"[{self.name}] Input 'in' shape changed: expected {self._resolved_shape}, got {u.shape}."
            )
