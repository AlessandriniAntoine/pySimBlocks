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


class DiscreteDerivator(Block):
    """Discrete-time differentiator block.

    Estimates the derivative of the input using a backward finite difference:

        y[k] = (u[k] - u[k-1]) / dt

    The output shape is resolved from the first non-scalar input and then
    frozen. If an ``initial_output`` is provided it immediately fixes the shape.
    A scalar (1,1) input is broadcast to the frozen shape once it is known.
    The output is never ``None`` — a zero placeholder is used when no shape
    information is yet available.

    Attributes:
        initial_output: Initial output value, or None if not provided.
    """

    direct_feedthrough = True

    def __init__(
        self,
        name: str,
        initial_output: ArrayLike | None = None,
        sample_time: float | None = None,
    ):
        """Initialize a DiscreteDerivator block.

        Args:
            name: Unique identifier for this block instance.
            initial_output: Output used at the first execution step. If
                provided, it also fixes the signal shape permanently.
            sample_time: Sampling period in seconds, or None to use the global
                simulation dt.
        """
        super().__init__(name, sample_time)

        self.inputs["in"] = None
        self.outputs["out"] = None

        self.state["u_prev"] = None
        self.next_state["u_prev"] = None

        self._resolved_shape: tuple[int, int] | None = None
        self._first_output = True

        self._placeholder = np.zeros((1, 1), dtype=float)

        self._initial_output_raw: np.ndarray | None = None
        if initial_output is not None:
            y0 = self._to_2d_array("initial_output", initial_output).astype(float)
            self._initial_output_raw = y0.copy()

            self._resolved_shape = y0.shape
            self.outputs["out"] = y0.copy()
        else:
            self.outputs["out"] = self._placeholder.copy()


    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------

    def initialize(self, t0: float) -> None:
        """Set the previous-input state and prepare the initial output.

        Args:
            t0: Initial simulation time in seconds.
        """
        u = self.inputs["in"]

        if u is None:
            self.state["u_prev"] = None
            self.next_state["u_prev"] = None
            self._first_output = True
            return

        u_arr = self._normalize_input(u)

        self.state["u_prev"] = u_arr.copy()
        self.next_state["u_prev"] = u_arr.copy()
        self._first_output = True

    def output_update(self, t: float, dt: float) -> None:
        """Compute the finite-difference derivative and write it to the output port.

        At the first call the output is held at ``initial_output`` (or zero if
        none was provided). Afterwards:

            y = (u - u_prev) / dt

        Args:
            t: Current simulation time in seconds.
            dt: Current time step in seconds.
        """
        u_arr = self._normalize_input(self.inputs["in"])

        if self._first_output:
            self._first_output = False
            if self._resolved_shape is not None and self.outputs["out"] is not None:
                y = np.asarray(self.outputs["out"], dtype=float)
                if y.shape == (1, 1) and self._resolved_shape != (1, 1):
                    self.outputs["out"] = np.full(self._resolved_shape, float(y[0, 0]), dtype=float)
            return

        u_prev = self.state["u_prev"]
        if u_prev is None:
            self.outputs["out"] = np.zeros_like(u_arr)
            return

        u_prev_arr = np.asarray(u_prev, dtype=float)
        if self._resolved_shape is not None and u_prev_arr.shape == (1, 1) and self._resolved_shape != (1, 1):
            u_prev_arr = np.full(self._resolved_shape, float(u_prev_arr[0, 0]), dtype=float)

        if u_prev_arr.shape != u_arr.shape:
            raise ValueError(
                f"[{self.name}] Previous input shape mismatch: u_prev={u_prev_arr.shape}, u={u_arr.shape}."
            )

        self.outputs["out"] = (u_arr - u_prev_arr) / dt

    def state_update(self, t: float, dt: float) -> None:
        """Store the current input as the previous value for the next step.

        Args:
            t: Current simulation time in seconds.
            dt: Current time step in seconds.
        """
        u_arr = self._normalize_input(self.inputs["in"])
        self.next_state["u_prev"] = u_arr.copy()


    # --------------------------------------------------------------------------
    # Private methods
    # --------------------------------------------------------------------------

    def _maybe_freeze_shape_from(self, u: np.ndarray) -> None:
        """Freeze the signal shape from the first non-scalar input."""
        if u.ndim != 2:
            raise ValueError(
                f"[{self.name}] Input 'in' must be a 2D array. Got ndim={u.ndim} with shape {u.shape}."
            )

        if self._resolved_shape is not None:
            return

        if u.shape != (1, 1):
            self._resolved_shape = u.shape

            y = np.asarray(self.outputs["out"], dtype=float)
            if y.shape == (1, 1):
                scalar = float(y[0, 0])
                self.outputs["out"] = np.full(self._resolved_shape, scalar, dtype=float)

            self.state["u_prev"] = u.copy()
            self.next_state["u_prev"] = u.copy()

    def _normalize_input(self, u: ArrayLike | None) -> np.ndarray:
        """Normalize input to 2D, applying shape freezing and scalar broadcasting."""
        if u is None:
            if self._resolved_shape is not None:
                return np.zeros(self._resolved_shape, dtype=float)
            return self._placeholder.copy()

        u_arr = np.asarray(u, dtype=float)
        if u_arr.ndim != 2:
            raise ValueError(
                f"[{self.name}] Input 'in' must be a 2D array. Got ndim={u_arr.ndim} with shape {u_arr.shape}."
            )

        self._maybe_freeze_shape_from(u_arr)

        if self._resolved_shape is not None:
            if u_arr.shape == (1, 1) and self._resolved_shape != (1, 1):
                return np.full(self._resolved_shape, float(u_arr[0, 0]), dtype=float)

            if u_arr.shape != self._resolved_shape:
                raise ValueError(
                    f"[{self.name}] Input 'in' shape changed: expected {self._resolved_shape}, got {u_arr.shape}."
                )

        return u_arr
