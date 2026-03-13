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
from numpy.typing import ArrayLike

from pySimBlocks.core.block import Block


class DeadZone(Block):
    """Discrete-time dead-zone operator.

    Suppresses the input within a specified interval and shifts the signal
    outside it:

        y = 0                    if lower_bound <= u <= upper_bound

        y = u - upper_bound      if u > upper_bound

        y = u - lower_bound      if u < lower_bound

    Bounds are applied component-wise and resolved on the first call. Once the
    input shape is resolved it must remain constant.

    Attributes:
        lower_raw: Raw lower bound array before broadcasting.
        upper_raw: Raw upper bound array before broadcasting.
        lower_bound: Broadcasted lower bound matched to the input shape, or
            None before the first resolution.
        upper_bound: Broadcasted upper bound matched to the input shape, or
            None before the first resolution.
    """

    direct_feedthrough = True

    def __init__(
        self,
        name: str,
        lower_bound: ArrayLike = 0.0,
        upper_bound: ArrayLike = 0.0,
        sample_time: float | None = None,
    ):
        """Initialize a DeadZone block.

        Args:
            name: Unique identifier for this block instance.
            lower_bound: Lower bound of the dead zone. Must be <= 0
                component-wise. Accepted shapes: scalar, 1D vector, or 2D
                matrix.
            upper_bound: Upper bound of the dead zone. Must be >= 0
                component-wise. Accepted shapes: scalar, 1D vector, or 2D
                matrix.
            sample_time: Sampling period in seconds, or None to use the global
                simulation dt.

        Raises:
            ValueError: If bounds cannot be converted to a 2D array.
        """
        super().__init__(name, sample_time)

        self.inputs["in"] = None
        self.outputs["out"] = None

        self.lower_raw = self._to_2d_array("lower_bound", lower_bound)
        self.upper_raw = self._to_2d_array("upper_bound", upper_bound)

        self.lower_bound = None
        self.upper_bound = None
        self._resolved_shape: tuple[int, int] | None = None


    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------

    def initialize(self, t0: float) -> None:
        """Resolve bounds from the initial input and compute the initial output.

        Args:
            t0: Initial simulation time in seconds.

        Raises:
            RuntimeError: If input ``'in'`` is None at initialization.
            ValueError: If input is not 2D or bounds have incompatible shapes.
        """
        u = self.inputs["in"]
        if u is None:
            raise RuntimeError(f"[{self.name}] Input 'in' is None at initialization.")

        u = np.asarray(u, dtype=float)
        if u.ndim != 2:
            raise ValueError(
                f"[{self.name}] Input 'in' must be a 2D array. Got ndim={u.ndim} with shape {u.shape}."
            )

        self._resolve_for_input(u)
        self.outputs["out"] = self._apply_dead_zone(u)

    def output_update(self, t: float, dt: float) -> None:
        """Apply the dead zone to the input and write the result to the output port.

        Args:
            t: Current simulation time in seconds.
            dt: Current time step in seconds.

        Raises:
            RuntimeError: If input ``'in'`` is None.
            ValueError: If input is not 2D or its shape changed after
                initialization.
        """
        u = self.inputs["in"]
        if u is None:
            raise RuntimeError(f"[{self.name}] Input 'in' is None.")

        u = np.asarray(u, dtype=float)
        if u.ndim != 2:
            raise ValueError(
                f"[{self.name}] Input 'in' must be a 2D array. Got ndim={u.ndim} with shape {u.shape}."
            )

        self._resolve_for_input(u)
        self.outputs["out"] = self._apply_dead_zone(u)

    def state_update(self, t: float, dt: float) -> None:
        """No-op: DeadZone is a stateless block.

        Args:
            t: Current simulation time in seconds.
            dt: Current time step in seconds.
        """
        return


    # --------------------------------------------------------------------------
    # Private methods
    # --------------------------------------------------------------------------

    def _broadcast_bound(self, b: np.ndarray, target_shape: tuple[int, int], name: str) -> np.ndarray:
        """Broadcast a bound array to the target input shape."""
        m, n = target_shape

        if self._is_scalar_2d(b):
            return np.full(target_shape, float(b[0, 0]), dtype=float)

        if b.ndim == 2 and b.shape[1] == 1 and b.shape[0] == m:
            if n == 1:
                return b.astype(float, copy=False)
            return np.repeat(b.astype(float, copy=False), n, axis=1)

        if b.shape == target_shape:
            return b.astype(float, copy=False)

        raise ValueError(
            f"[{self.name}] {name} has incompatible shape {b.shape} for input shape {target_shape}. "
            f"Allowed: scalar (1,1), vector (m,1), or matrix (m,n)."
        )

    def _resolve_for_input(self, u: np.ndarray) -> None:
        """Broadcast and validate bounds against the input shape on first call."""
        if u.ndim != 2:
            raise ValueError(
                f"[{self.name}] Input 'in' must be a 2D array. Got ndim={u.ndim} with shape {u.shape}."
            )

        if self._resolved_shape is None:
            self._resolved_shape = u.shape
            self.lower_bound = self._broadcast_bound(self.lower_raw, u.shape, "lower_bound")
            self.upper_bound = self._broadcast_bound(self.upper_raw, u.shape, "upper_bound")

            if np.any(self.lower_bound > self.upper_bound):
                raise ValueError(f"[{self.name}] lower_bound must be <= upper_bound (component-wise).")
            if np.any(self.lower_bound > 0):
                raise ValueError(f"[{self.name}] lower_bound must be <= 0 (component-wise).")
            if np.any(self.upper_bound < 0):
                raise ValueError(f"[{self.name}] upper_bound must be >= 0 (component-wise).")

            return

        if u.shape != self._resolved_shape:
            raise ValueError(
                f"[{self.name}] Input 'in' shape changed after initialization: "
                f"expected {self._resolved_shape}, got {u.shape}."
            )

    def _apply_dead_zone(self, u: np.ndarray) -> np.ndarray:
        """Compute the dead-zone output for a validated input array."""
        y = np.zeros_like(u)

        above = u > self.upper_bound
        below = u < self.lower_bound

        y[above] = u[above] - self.upper_bound[above]
        y[below] = u[below] - self.lower_bound[below]

        return y
