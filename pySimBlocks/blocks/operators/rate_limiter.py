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


class RateLimiter(Block):
    """Discrete-time rate limiter block.

    Limits the rate of change of the output signal by constraining the maximum
    allowed increase and decrease per time step:

        delta  = u[k] - y[k-1]

        y[k]   = y[k-1] + clip(delta, falling_slope * dt, rising_slope * dt)

    Bounds are applied component-wise and resolved on the first call. Once the
    input shape is resolved it must remain constant.

    Attributes:
        rising_raw: Raw rising-slope array before broadcasting.
        falling_raw: Raw falling-slope array before broadcasting.
        rising_slope: Broadcasted rising slope matched to the input shape, or
            None before the first resolution.
        falling_slope: Broadcasted falling slope matched to the input shape, or
            None before the first resolution.
    """

    direct_feedthrough = True

    def __init__(
        self,
        name: str,
        rising_slope: ArrayLike = np.inf,
        falling_slope: ArrayLike = -np.inf,
        initial_output: ArrayLike | None = None,
        sample_time: float | None = None,
    ):
        """Initialize a RateLimiter block.

        Args:
            name: Unique identifier for this block instance.
            rising_slope: Maximum allowed positive rate of change (>= 0).
                Accepted shapes: scalar, 1D vector, or 2D matrix.
            falling_slope: Maximum allowed negative rate of change (<= 0).
                Accepted shapes: scalar, 1D vector, or 2D matrix.
            initial_output: Initial output y(-1). If not provided, y(-1) is
                set to the first input u(0).
            sample_time: Sampling period in seconds, or None to use the global
                simulation dt.

        Raises:
            ValueError: If ``rising_slope`` has a negative component or
                ``falling_slope`` has a positive component.
        """
        super().__init__(name, sample_time)

        self.inputs["in"] = None
        self.outputs["out"] = None

        self.rising_raw = self._to_2d_array("rising_slope", rising_slope)
        self.falling_raw = self._to_2d_array("falling_slope", falling_slope)
        self.y0_raw = None if initial_output is None else self._to_2d_array("initial_output", initial_output)

        if np.any(self.rising_raw < 0):
            raise ValueError(f"[{self.name}] rising_slope must be >= 0.")
        if np.any(self.falling_raw > 0):
            raise ValueError(f"[{self.name}] falling_slope must be <= 0.")

        self.rising_slope: ArrayLike | None = None
        self.falling_slope: ArrayLike | None = None
        self._resolved_shape: tuple[int, int] | None = None

        self.state["y"] = None
        self.next_state["y"] = None


    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------

    def initialize(self, t0: float) -> None:
        """Resolve slopes from the initial input and set the initial state.

        Args:
            t0: Initial simulation time in seconds.

        Raises:
            RuntimeError: If input ``'in'`` is None at initialization.
            ValueError: If input is not 2D or slopes have incompatible shapes.
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

        if self.y0_raw is not None:
            y0 = self._broadcast_param(self.y0_raw, u.shape, "initial_output")
        else:
            y0 = u.copy()

        self.state["y"] = y0.copy()
        self.outputs["out"] = y0.copy()

    def output_update(self, t: float, dt: float) -> None:
        """Apply the rate limit and write the result to the output port.

        Args:
            t: Current simulation time in seconds.
            dt: Current time step in seconds.

        Raises:
            RuntimeError: If input ``'in'`` is None or the block is not
                initialized.
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

        if self.state["y"] is None:
            raise RuntimeError(f"[{self.name}] RateLimiter not initialized (state 'y' is None).")

        self._resolve_for_input(u)

        y_prev = self.state["y"]
        if y_prev.shape != u.shape:
            raise ValueError(
                f"[{self.name}] Internal state shape mismatch: y has shape {y_prev.shape}, input has shape {u.shape}."
            )

        du = u - y_prev
        du_min = self.falling_slope * dt
        du_max = self.rising_slope * dt

        du_limited = np.clip(du, du_min, du_max)
        self.outputs["out"] = y_prev + du_limited

    def state_update(self, t: float, dt: float) -> None:
        """Store the current output as the previous value for the next step.

        Args:
            t: Current simulation time in seconds.
            dt: Current time step in seconds.
        """
        self.next_state["y"] = None if self.outputs["out"] is None else self.outputs["out"].copy()


    # --------------------------------------------------------------------------
    # Private methods
    # --------------------------------------------------------------------------

    def _broadcast_param(self, p: np.ndarray, target_shape: tuple[int, int], name: str) -> np.ndarray:
        """Broadcast a parameter array to the target input shape."""
        m, n = target_shape

        if self._is_scalar_2d(p):
            return np.full(target_shape, float(p[0, 0]), dtype=float)

        if p.ndim == 2 and p.shape[1] == 1 and p.shape[0] == m:
            if n == 1:
                return p.astype(float, copy=False)
            return np.repeat(p.astype(float, copy=False), n, axis=1)

        if p.shape == target_shape:
            return p.astype(float, copy=False)

        raise ValueError(
            f"[{self.name}] {name} has incompatible shape {p.shape} for input shape {target_shape}. "
            f"Allowed: scalar (1,1), vector (m,1), or matrix (m,n)."
        )

    def _resolve_for_input(self, u: np.ndarray) -> None:
        """Broadcast and validate slopes against the input shape on first call."""
        if u.ndim != 2:
            raise ValueError(
                f"[{self.name}] Input 'in' must be a 2D array. Got ndim={u.ndim} with shape {u.shape}."
            )

        if self._resolved_shape is None:
            self._resolved_shape = u.shape
            self.rising_slope = self._broadcast_param(self.rising_raw, u.shape, "rising_slope")
            self.falling_slope = self._broadcast_param(self.falling_raw, u.shape, "falling_slope")

            if np.any(self.rising_slope < 0):
                raise ValueError(f"[{self.name}] rising_slope must be >= 0.")
            if np.any(self.falling_slope > 0):
                raise ValueError(f"[{self.name}] falling_slope must be <= 0.")
            return

        if u.shape != self._resolved_shape:
            raise ValueError(
                f"[{self.name}] Input 'in' shape changed after initialization: "
                f"expected {self._resolved_shape}, got {u.shape}."
            )
