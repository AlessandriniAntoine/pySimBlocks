# ******************************************************************************
#                                  pySimBlocks
#                     Copyright (c) 2026 Antoine Alessandrini
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

import numpy as np
from numpy.typing import ArrayLike

from pySimBlocks.core.block import Block


class DeadZone(Block):
    """
    Discrete-time dead zone operator.

    Summary:
        Suppresses the input signal within a specified interval around zero
        and shifts the signal outside this interval.

    Parameters:
        lower_bound : scalar or array-like
            Lower bound of the dead zone (must be <= 0 component-wise).
        upper_bound : scalar or array-like
            Upper bound of the dead zone (must be >= 0 component-wise).
        sample_time : float, optional
            Block execution period.

    Inputs:
        in : array (m,n)
            Input signal (must be 2D).

    Outputs:
        out : array (m,n)
            Output signal after dead-zone transformation.

    Notes:
        - Stateless block.
        - Direct feedthrough.
        - Bounds are applied component-wise.
        - Broadcasting rules (to match input shape (m,n)):
            * scalar (1,1) broadcasts to (m,n)
            * vector (m,1) broadcasts across columns to (m,n)
            * matrix (m,n) must match exactly
        - The dead zone must include zero component-wise:
            lower_bound <= 0 <= upper_bound.
        - Once resolved, input shape must remain constant.
    """

    direct_feedthrough = True

    def __init__(
        self,
        name: str,
        lower_bound: ArrayLike = 0.0,
        upper_bound: ArrayLike = 0.0,
        sample_time: float | None = None,
    ):
        super().__init__(name, sample_time)

        self.inputs["in"] = None
        self.outputs["out"] = None

        self.lower_raw = self._to_2d_array("lower_bound", lower_bound)
        self.upper_raw = self._to_2d_array("upper_bound", upper_bound)

        self.lower_bound = None
        self.upper_bound = None
        self._resolved_shape: tuple[int, int] | None = None


    # --------------------------------------------------------------------------
    # Private methods
    # --------------------------------------------------------------------------
    def initialize(self, t0: float) -> None:
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

    # ------------------------------------------------------------------
    def output_update(self, t: float, dt: float) -> None:
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

    # ------------------------------------------------------------------
    def state_update(self, t: float, dt: float) -> None:
        return  # stateless


    # --------------------------------------------------------------------------
    # Private methods
    # --------------------------------------------------------------------------
    def _broadcast_bound(self, b: np.ndarray, target_shape: tuple[int, int], name: str) -> np.ndarray:
        m, n = target_shape

        # scalar -> full matrix
        if self._is_scalar_2d(b):
            return np.full(target_shape, float(b[0, 0]), dtype=float)

        # vector (m,1) -> broadcast across columns
        if b.ndim == 2 and b.shape[1] == 1 and b.shape[0] == m:
            if n == 1:
                return b.astype(float, copy=False)
            return np.repeat(b.astype(float, copy=False), n, axis=1)

        # matrix -> must match exactly
        if b.shape == target_shape:
            return b.astype(float, copy=False)

        raise ValueError(
            f"[{self.name}] {name} has incompatible shape {b.shape} for input shape {target_shape}. "
            f"Allowed: scalar (1,1), vector (m,1), or matrix (m,n)."
        )

    # ------------------------------------------------------------------
    def _resolve_for_input(self, u: np.ndarray) -> None:
        if u.ndim != 2:
            raise ValueError(
                f"[{self.name}] Input 'in' must be a 2D array. Got ndim={u.ndim} with shape {u.shape}."
            )

        if self._resolved_shape is None:
            self._resolved_shape = u.shape
            self.lower_bound = self._broadcast_bound(self.lower_raw, u.shape, "lower_bound")
            self.upper_bound = self._broadcast_bound(self.upper_raw, u.shape, "upper_bound")

            # Component-wise validity checks (after broadcasting)
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

    # ------------------------------------------------------------------
    def _apply_dead_zone(self, u: np.ndarray) -> np.ndarray:
        y = np.zeros_like(u)

        above = u > self.upper_bound
        below = u < self.lower_bound

        y[above] = u[above] - self.upper_bound[above]
        y[below] = u[below] - self.lower_bound[below]

        return y
