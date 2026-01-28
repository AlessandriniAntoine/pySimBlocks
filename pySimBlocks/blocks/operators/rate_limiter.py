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


class RateLimiter(Block):
    """
    Discrete-time rate limiter block.

    Summary:
        Limits the rate of change of the output signal by constraining the
        maximum allowed increase and decrease per time step.

    Parameters:
        rising_slope : scalar or array-like, optional
            Maximum allowed positive rate of change (>= 0).
        falling_slope : scalar or array-like, optional
            Maximum allowed negative rate of change (<= 0).
        initial_output : scalar or array-like, optional
            Initial output y(-1). If not provided, y(-1) = u(0).
        sample_time : float, optional
            Block execution period.

    Inputs:
        in : array (m,n)
            Input signal (must be 2D).

    Outputs:
        out : array (m,n)
            Rate-limited output signal.

    Notes:
        - Stateful block.
        - Direct feedthrough.
        - Broadcasting rules (to match input shape (m,n)):
            * scalar (1,1) broadcasts to (m,n)
            * vector (m,1) broadcasts across columns to (m,n)
            * matrix (m,n) must match exactly
        - Once resolved, input shape must remain constant.
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
        super().__init__(name, sample_time)

        self.inputs["in"] = None
        self.outputs["out"] = None

        # Raw parameters (2D normalized)
        self.rising_raw = self._to_2d_array("rising_slope", rising_slope)
        self.falling_raw = self._to_2d_array("falling_slope", falling_slope)
        self.y0_raw = None if initial_output is None else self._to_2d_array("initial_output", initial_output)

        # Basic sign constraints (raw)
        if np.any(self.rising_raw < 0):
            raise ValueError(f"[{self.name}] rising_slope must be >= 0.")
        if np.any(self.falling_raw > 0):
            raise ValueError(f"[{self.name}] falling_slope must be <= 0.")

        # Resolved parameters (broadcasted to input shape once known)
        self.rising_slope: ArrayLike | None = None
        self.falling_slope: ArrayLike | None  = None
        self._resolved_shape: tuple[int, int] | None = None

        # State
        self.state["y"] = None
        self.next_state["y"] = None


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

        self._resolve_for_input(u)

        if self.y0_raw is not None:
            y0 = self._broadcast_param(self.y0_raw, u.shape, "initial_output")
        else:
            y0 = u.copy()

        self.state["y"] = y0.copy()
        self.outputs["out"] = y0.copy()

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

        if self.state["y"] is None:
            raise RuntimeError(f"[{self.name}] RateLimiter not initialized (state 'y' is None).")

        self._resolve_for_input(u)

        y_prev = self.state["y"]
        if y_prev.shape != u.shape:
            # extra safety: state shape must match input shape
            raise ValueError(
                f"[{self.name}] Internal state shape mismatch: y has shape {y_prev.shape}, input has shape {u.shape}."
            )

        du = u - y_prev
        du_min = self.falling_slope * dt
        du_max = self.rising_slope * dt

        du_limited = np.clip(du, du_min, du_max)
        self.outputs["out"] = y_prev + du_limited

    # ------------------------------------------------------------------
    def state_update(self, t: float, dt: float) -> None:
        self.next_state["y"] = None if self.outputs["out"] is None else self.outputs["out"].copy()


    # --------------------------------------------------------------------------
    # Private methods
    # --------------------------------------------------------------------------
    def _broadcast_param(self, p: np.ndarray, target_shape: tuple[int, int], name: str) -> np.ndarray:
        """
        Broadcast p to target_shape using explicit rules:
            - scalar (1,1) -> (m,n)
            - vector (m,1) -> repeat along columns to (m,n)
            - matrix (m,n) -> exact match
        """
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

    # ------------------------------------------------------------------
    def _resolve_for_input(self, u: np.ndarray) -> None:
        """
        Resolve (broadcast) slopes and initial_output to match the current input shape.
        Done once. After that, input shape is fixed.
        """
        if u.ndim != 2:
            raise ValueError(
                f"[{self.name}] Input 'in' must be a 2D array. Got ndim={u.ndim} with shape {u.shape}."
            )

        if self._resolved_shape is None:
            self._resolved_shape = u.shape
            self.rising_slope = self._broadcast_param(self.rising_raw, u.shape, "rising_slope")
            self.falling_slope = self._broadcast_param(self.falling_raw, u.shape, "falling_slope")

            # Re-check signs after broadcasting (useful if vector/matrix provided)
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
