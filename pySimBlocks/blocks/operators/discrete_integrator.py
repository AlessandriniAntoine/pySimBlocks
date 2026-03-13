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


class DiscreteIntegrator(Block):
    """Discrete-time integrator block.

    Integrates an input signal over time using either Euler forward or Euler
    backward integration. The state update is:

        x[k+1] = x[k] + dt * u[k]

    The output differs by method:

        y[k] = x[k]                   (Euler forward)

        y[k] = x[k] + dt * u[k]       (Euler backward)

    Euler forward has no direct feedthrough; Euler backward does. The output
    shape is resolved from the first non-scalar input and then frozen. A scalar
    (1,1) input is broadcast to the frozen shape. The output is never ``None``.

    Attributes:
        method: Integration method, ``'euler forward'`` or ``'euler backward'``.
    """

    def __init__(
        self,
        name: str,
        initial_state: ArrayLike | None = None,
        method: str = "euler forward",
        sample_time: float | None = None,
    ):
        """Initialize a DiscreteIntegrator block.

        Args:
            name: Unique identifier for this block instance.
            initial_state: Initial value of the integrated state. If provided
                and non-scalar, it fixes the signal shape immediately.
            method: Integration method. Either ``'euler forward'`` or
                ``'euler backward'``.
            sample_time: Sampling period in seconds, or None to use the global
                simulation dt.

        Raises:
            ValueError: If ``method`` is not ``'euler forward'`` or
                ``'euler backward'``.
        """
        super().__init__(name, sample_time)

        self.method = method.lower()
        if self.method not in ("euler forward", "euler backward"):
            raise ValueError(
                f"[{self.name}] Unsupported method '{method}'. "
                f"Allowed: 'euler forward', 'euler backward'."
            )

        self.direct_feedthrough = (self.method == "euler backward")

        self.inputs["in"] = None
        self.outputs["out"] = None

        self._resolved_shape: tuple[int, int] | None = None

        self.state["x"] = None
        self.next_state["x"] = None

        self._placeholder = np.zeros((1, 1), dtype=float)

        self._initial_state_raw: np.ndarray | None = None
        if initial_state is not None:
            x0 = self._to_2d_array("initial_state", initial_state).astype(float)
            self._initial_state_raw = x0.copy()

            if x0.shape != (1, 1):
                self._resolved_shape = x0.shape

            self.state["x"] = x0.copy()
            self.next_state["x"] = x0.copy()
            self.outputs["out"] = x0.copy()
        else:
            self.state["x"] = self._placeholder.copy()
            self.next_state["x"] = self._placeholder.copy()
            self.outputs["out"] = self._placeholder.copy()


    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------

    def initialize(self, t0: float) -> None:
        """Set the initial state and output from ``initial_state`` or a zero placeholder.

        Args:
            t0: Initial simulation time in seconds.
        """
        if self._initial_state_raw is not None:
            x0 = self._initial_state_raw.copy()
            self.state["x"] = x0.copy()
            self.next_state["x"] = x0.copy()
            self.outputs["out"] = x0.copy()
        else:
            self.state["x"] = self._placeholder.copy()
            self.next_state["x"] = self._placeholder.copy()
            self.outputs["out"] = self._placeholder.copy()

    def output_update(self, t: float, dt: float) -> None:
        """Compute the output from the current state according to the integration method.

        Args:
            t: Current simulation time in seconds.
            dt: Current time step in seconds.
        """
        x = self._normalize_state()

        if self.method == "euler forward":
            self.outputs["out"] = x.copy()
            return

        u = self._normalize_input(self.inputs["in"])
        self.outputs["out"] = x + dt * u

    def state_update(self, t: float, dt: float) -> None:
        """Advance the integrator state by one step.

        Args:
            t: Current simulation time in seconds.
            dt: Current time step in seconds.

        Raises:
            ValueError: If the state and input shapes are inconsistent after
                shape resolution.
        """
        u = self._normalize_input(self.inputs["in"])
        x = self._normalize_state()

        if self._resolved_shape is not None:
            if x.shape != u.shape:
                raise ValueError(
                    f"[{self.name}] Shape mismatch between state and input: x={x.shape}, u={u.shape}."
                )

        self.next_state["x"] = x + dt * u


    # --------------------------------------------------------------------------
    # Private methods
    # --------------------------------------------------------------------------

    def _maybe_freeze_shape_from(self, u: np.ndarray) -> None:
        """Freeze the signal shape from the first non-scalar input."""
        if u.ndim != 2:
            raise ValueError(
                f"[{self.name}] Input 'in' must be a 2D array. Got ndim={u.ndim} with shape {u.shape}."
            )

        if self._resolved_shape is None and u.shape != (1, 1):
            self._resolved_shape = u.shape

            if self.state["x"] is None:
                self.state["x"] = np.zeros(self._resolved_shape, dtype=float)
            else:
                x = np.asarray(self.state["x"], dtype=float)
                if x.shape == (1, 1):
                    scalar = float(x[0, 0])
                    self.state["x"] = np.full(self._resolved_shape, scalar, dtype=float)

            self.next_state["x"] = np.asarray(self.state["x"], dtype=float).copy()

            y = np.asarray(self.outputs["out"], dtype=float)
            if y.shape == (1, 1):
                scalar = float(y[0, 0])
                self.outputs["out"] = np.full(self._resolved_shape, scalar, dtype=float)

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

    def _normalize_state(self) -> np.ndarray:
        """Ensure the state exists and matches the resolved shape."""
        x = np.asarray(self.state["x"], dtype=float)

        if self._resolved_shape is not None and self._resolved_shape != (1, 1):
            if x.shape == (1, 1):
                scalar = float(x[0, 0])
                x = np.full(self._resolved_shape, scalar, dtype=float)
                self.state["x"] = x.copy()

            if x.shape != self._resolved_shape:
                raise ValueError(
                    f"[{self.name}] State shape mismatch: expected {self._resolved_shape}, got {x.shape}."
                )

        return x
