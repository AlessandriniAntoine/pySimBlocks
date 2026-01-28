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


class Saturation(Block):
    """
    Discrete-time saturation operator.

    Summary:
        Applies element-wise saturation to the input signal by enforcing
        lower and upper bounds.

    Parameters:
        u_min : scalar or array-like, optional
            Lower saturation bound.
            Accepted: scalar -> (1,1), 1D -> (m,1), 2D -> (m,n).
            Broadcasting rules are limited and explicit (see Notes).
        u_max : scalar or array-like, optional
            Upper saturation bound.
        sample_time : float, optional
            Block execution period.

    Inputs:
        in : array (m,n)
            Input signal (must be 2D).

    Outputs:
        out : array (m,n)
            Saturated output signal.

    Notes:
        - Stateless block.
        - Direct feedthrough.
        - Input must be 2D. No implicit reshape/flatten.
        - Broadcasting rules for bounds (to match input shape (m,n)):
            * scalar (1,1) broadcasts to (m,n)
            * vector (m,1) broadcasts across columns to (m,n)
            * matrix (m,n) must match exactly
        - Any other shape mismatch raises ValueError.
    """

    direct_feedthrough = True

    def __init__(
        self,
        name: str,
        u_min: ArrayLike = -np.inf,
        u_max: ArrayLike = np.inf,
        sample_time: float | None = None,
    ):
        super().__init__(name, sample_time)

        self.inputs["in"] = None
        self.outputs["out"] = None

        self.u_min_raw = self._to_2d_array("u_min", u_min)
        self.u_max_raw = self._to_2d_array("u_max", u_max)

        # These will become "resolved" (broadcasted) once we know input shape
        self.u_min = None
        self.u_max = None
        self._resolved_shape: tuple[int, int] | None = None


    # --------------------------------------------------------------------------
    # Public methods
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

        self._resolve_bounds_for_input(u)
        self.outputs["out"] = np.clip(u, self.u_min, self.u_max)

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

        self._resolve_bounds_for_input(u)
        self.outputs["out"] = np.clip(u, self.u_min, self.u_max)

    # ------------------------------------------------------------------
    def state_update(self, t: float, dt: float) -> None:
        return  # stateless


    # --------------------------------------------------------------------------
    # Private methods
    # --------------------------------------------------------------------------
    def _resolve_bounds_for_input(self, u: np.ndarray) -> None:
        """
        Resolve (broadcast) u_min/u_max to match the current input shape.
        Resolution is done once (first time input is available). After that,
        input shape is expected to remain constant.
        """
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

        # Already resolved => enforce constant input shape
        if u.shape != self._resolved_shape:
            raise ValueError(
                f"[{self.name}] Input 'in' shape changed after bounds were resolved: "
                f"expected {self._resolved_shape}, got {u.shape}."
            )

    def _broadcast_bound(self, b: np.ndarray, target_shape: tuple[int, int], name: str) -> np.ndarray:
        """
        Broadcast bound b to target_shape using explicit rules.
        """
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
