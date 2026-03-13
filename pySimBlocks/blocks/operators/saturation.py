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


class Saturation(Block):
    """Discrete-time saturation operator.

    Applies element-wise saturation to the input signal:

        y = clip(u, u_min, u_max)

    Bounds are resolved component-wise on the first call using explicit
    broadcasting rules: scalar (1,1) broadcasts to (m,n); vector (m,1)
    broadcasts across columns; matrix (m,n) must match exactly. Once the
    input shape is resolved it must remain constant.

    Attributes:
        u_min_raw: Raw lower bound before broadcasting.
        u_max_raw: Raw upper bound before broadcasting.
        u_min: Broadcasted lower bound matched to the input shape, or None
            before the first resolution.
        u_max: Broadcasted upper bound matched to the input shape, or None
            before the first resolution.
    """

    direct_feedthrough = True

    def __init__(
        self,
        name: str,
        u_min: ArrayLike = -np.inf,
        u_max: ArrayLike = np.inf,
        sample_time: float | None = None,
    ):
        """Initialize a Saturation block.

        Args:
            name: Unique identifier for this block instance.
            u_min: Lower saturation bound. Accepted shapes: scalar, 1D vector,
                or 2D matrix.
            u_max: Upper saturation bound. Accepted shapes: scalar, 1D vector,
                or 2D matrix.
            sample_time: Sampling period in seconds, or None to use the global
                simulation dt.
        """
        super().__init__(name, sample_time)

        self.inputs["in"] = None
        self.outputs["out"] = None

        self.u_min_raw = self._to_2d_array("u_min", u_min)
        self.u_max_raw = self._to_2d_array("u_max", u_max)

        self.u_min = None
        self.u_max = None
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
            ValueError: If input is not 2D, bounds have incompatible shapes,
                or ``u_min > u_max`` for any component.
        """
        u = self.inputs["in"]
        if u is None:
            raise RuntimeError(f"[{self.name}] Input 'in' is None at initialization.")

        u = np.asarray(u, dtype=float)
        if u.ndim != 2:
            raise ValueError(
                f"[{self.name}] Input 'in' must be a 2D array. Got ndim={u.ndim} with shape {u.shape}."
            )

        self._resolve_bounds_for_input(u)
        self.outputs["out"] = np.clip(u, self.u_min, self.u_max)

    def output_update(self, t: float, dt: float) -> None:
        """Saturate the input and write the result to the output port.

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

        self._resolve_bounds_for_input(u)
        self.outputs["out"] = np.clip(u, self.u_min, self.u_max)

    def state_update(self, t: float, dt: float) -> None:
        """No-op: Saturation is a stateless block.

        Args:
            t: Current simulation time in seconds.
            dt: Current time step in seconds.
        """
        return


    # --------------------------------------------------------------------------
    # Private methods
    # --------------------------------------------------------------------------

    def _resolve_bounds_for_input(self, u: np.ndarray) -> None:
        """Broadcast and validate bounds against the input shape on first call."""
        if u.ndim != 2:
            raise ValueError(
                f"[{self.name}] Input 'in' must be a 2D array. Got ndim={u.ndim} with shape {u.shape}."
            )

        if self._resolved_shape is None:
            self._resolved_shape = u.shape

            self.u_min = self._broadcast_bound(self.u_min_raw, u.shape, "u_min")
            self.u_max = self._broadcast_bound(self.u_max_raw, u.shape, "u_max")

            if np.any(self.u_min > self.u_max):
                raise ValueError(f"[{self.name}] u_min must be <= u_max for all components.")
            return

        if u.shape != self._resolved_shape:
            raise ValueError(
                f"[{self.name}] Input 'in' shape changed after bounds were resolved: "
                f"expected {self._resolved_shape}, got {u.shape}."
            )

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
