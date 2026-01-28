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


class DiscreteDerivator(Block):
    """
    Discrete-time differentiator block.

    Summary:
        Estimates the discrete-time derivative of the input signal using a
        backward finite difference:
            y[k] = (u[k] - u[k-1]) / dt

    Parameters:
        initial_output : scalar or array-like, optional
            Output used at the first execution step.
            If provided, it also FIXES the signal shape permanently.
        sample_time : float, optional
            Block execution period.

    Inputs:
        in : array (m,n)
            Input signal (must be 2D).

    Outputs:
        out : array (m,n)
            Estimated discrete-time derivative.

    Notes:
        - Stateful block.
        - Direct feedthrough.
        - Shape is frozen as soon as known (initial_output or first input).
        - No implicit vector reshape; matrices are supported.
        - Policy:
            - Never propagate None: output is always at least (1,1) zeros.
            - Shape is unresolved while only scalar placeholder (1,1) is seen and no
              explicit initial_output is provided.
            - If initial_output is provided -> shape is frozen immediately (including (1,1)).
            - If no initial_output -> shape is frozen as soon as a non-scalar input arrives.
            - Once shape is frozen -> any non-scalar mismatch raises ValueError.
            - If shape frozen to (m,n) and input is scalar (1,1) -> broadcast scalar to (m,n).
            - When shape is frozen from a first non-scalar input, u_prev is initialized to
              that input to avoid bogus derivative spikes.
    """

    direct_feedthrough = True

    def __init__(
        self,
        name: str,
        initial_output: ArrayLike | None = None,
        sample_time: float | None = None,
    ):
        super().__init__(name, sample_time)

        self.inputs["in"] = None
        self.outputs["out"] = None

        self.state["u_prev"] = None
        self.next_state["u_prev"] = None

        self._resolved_shape: tuple[int, int] | None = None
        self._first_output = True

        # Never None: placeholder output at minimum
        self._placeholder = np.zeros((1, 1), dtype=float)

        self._initial_output_raw: np.ndarray | None = None
        if initial_output is not None:
            y0 = self._to_2d_array("initial_output", initial_output).astype(float)
            self._initial_output_raw = y0.copy()

            # initial_output freezes shape (including (1,1))
            self._resolved_shape = y0.shape
            self.outputs["out"] = y0.copy()
        else:
            self.outputs["out"] = self._placeholder.copy()


    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------
    def initialize(self, t0: float) -> None:
        """
        Never propagate None:
          - output already set (initial_output or placeholder (1,1)).
          - if input exists, we can set u_prev consistently.
          - if input missing, keep u_prev=None (or already set if frozen on first non-scalar later).
        """
        u = self.inputs["in"]

        if u is None:
            # Keep output as-is (initial_output or placeholder)
            self.state["u_prev"] = None
            self.next_state["u_prev"] = None
            self._first_output = True
            return

        u_arr = self._normalize_input(u)

        # If initial_output froze shape, _normalize_input enforces it.
        # Store u_prev to support derivative at next step.
        self.state["u_prev"] = u_arr.copy()
        self.next_state["u_prev"] = u_arr.copy()
        self._first_output = True

    # -------------------------------------------------------
    def output_update(self, t: float, dt: float) -> None:
        """
        First call policy:
          - If initial_output provided: keep it for first output_update.
          - Else: keep zero output for first call.

        Afterwards:
          y = (u - u_prev) / dt
        """
        u_arr = self._normalize_input(self.inputs["in"])

        if self._first_output:
            self._first_output = False
            # output already set (initial_output or placeholder); ensure shape if frozen
            if self._resolved_shape is not None and self.outputs["out"] is not None:
                y = np.asarray(self.outputs["out"], dtype=float)
                if y.shape == (1, 1) and self._resolved_shape != (1, 1):
                    self.outputs["out"] = np.full(self._resolved_shape, float(y[0, 0]), dtype=float)
            return

        u_prev = self.state["u_prev"]
        if u_prev is None:
            # No previous value -> define derivative as zero (same shape as u)
            self.outputs["out"] = np.zeros_like(u_arr)
            return

        # If shape frozen and u_prev is scalar, broadcast it
        u_prev_arr = np.asarray(u_prev, dtype=float)
        if self._resolved_shape is not None and u_prev_arr.shape == (1, 1) and self._resolved_shape != (1, 1):
            u_prev_arr = np.full(self._resolved_shape, float(u_prev_arr[0, 0]), dtype=float)

        if u_prev_arr.shape != u_arr.shape:
            raise ValueError(
                f"[{self.name}] Previous input shape mismatch: u_prev={u_prev_arr.shape}, u={u_arr.shape}."
            )

        self.outputs["out"] = (u_arr - u_prev_arr) / dt

    # -------------------------------------------------------
    def state_update(self, t: float, dt: float) -> None:
        u_arr = self._normalize_input(self.inputs["in"])
        self.next_state["u_prev"] = u_arr.copy()


    # --------------------------------------------------------------------------
    # Private methods
    # --------------------------------------------------------------------------
    def _maybe_freeze_shape_from(self, u: np.ndarray) -> None:
        """
        Freeze shape if:
          - no initial_output has already frozen it
          - shape unresolved
          - u is non-scalar (shape != (1,1))
        """
        if u.ndim != 2:
            raise ValueError(
                f"[{self.name}] Input 'in' must be a 2D array. Got ndim={u.ndim} with shape {u.shape}."
            )

        # If shape is already frozen (by initial_output), nothing to do
        if self._resolved_shape is not None:
            return

        # Only freeze when a non-scalar appears
        if u.shape != (1, 1):
            self._resolved_shape = u.shape

            # Upgrade current output placeholder to correct shape (keep current scalar value)
            y = np.asarray(self.outputs["out"], dtype=float)
            if y.shape == (1, 1):
                scalar = float(y[0, 0])
                self.outputs["out"] = np.full(self._resolved_shape, scalar, dtype=float)

            # Initialize u_prev to current u to avoid a derivative spike
            self.state["u_prev"] = u.copy()
            self.next_state["u_prev"] = u.copy()

    # -------------------------------------------------------
    def _normalize_input(self, u: ArrayLike | None) -> np.ndarray:
        """
        Normalize u to 2D, apply freezing rule and scalar broadcasting.
        If u is None: return zeros of resolved shape if known, else (1,1) zeros.
        """
        if u is None:
            if self._resolved_shape is not None:
                return np.zeros(self._resolved_shape, dtype=float)
            return self._placeholder.copy()

        u_arr = np.asarray(u, dtype=float)
        if u_arr.ndim != 2:
            raise ValueError(
                f"[{self.name}] Input 'in' must be a 2D array. Got ndim={u_arr.ndim} with shape {u_arr.shape}."
            )

        # If shape not frozen yet and u is non-scalar -> freeze now
        self._maybe_freeze_shape_from(u_arr)

        # If shape is frozen: enforce or broadcast
        if self._resolved_shape is not None:
            if u_arr.shape == (1, 1) and self._resolved_shape != (1, 1):
                return np.full(self._resolved_shape, float(u_arr[0, 0]), dtype=float)

            if u_arr.shape != self._resolved_shape:
                raise ValueError(
                    f"[{self.name}] Input 'in' shape changed: expected {self._resolved_shape}, got {u_arr.shape}."
                )

        return u_arr
