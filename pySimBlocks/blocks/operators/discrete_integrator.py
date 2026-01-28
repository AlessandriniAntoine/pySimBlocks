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


class DiscreteIntegrator(Block):
    """
    Discrete-time integrator block.

    Summary:
        Integrates an input signal over time using a discrete-time numerical
        integration scheme.

    Parameters:
        initial_state : scalar or array-like, optional
            Initial value of the integrated state. If provided, it FIXES the signal shape.
        method : str
            Numerical integration method: "euler forward" or "euler backward".
        sample_time : float, optional
            Block execution period.

    Inputs:
        in : array (m,n)
            Signal to integrate (must be 2D).

    Outputs:
        out : array (m,n)
            Integrated signal.

    Notes:
        - Stateful block.
        - Direct feedthrough depends on method:
            * euler forward  -> False
            * euler backward -> True
        - Shape is frozen as soon as known (initial_state or first input).
        - No implicit vector reshape; matrices are supported.
        - Policy:
            + Never propagate None: output is always a 2D array (at least (1,1)).
            + Shape is NOT frozen while we are in placeholder shape (1,1) and no explicit
              non-scalar initial_state was given.
            + As soon as a non-scalar input appears (shape != (1,1)), the shape becomes frozen.
            + If initial_state is provided and non-scalar, it freezes the shape immediately.
              If initial_state is scalar (1,1), it is treated as a placeholder: can be upgraded
              once a non-scalar input appears.
            + After shape is frozen, any non-scalar input shape mismatch raises ValueError.
            + If shape is frozen to (m,n), scalar input (1,1) is broadcast to (m,n).
    """

    def __init__(
        self,
        name: str,
        initial_state: ArrayLike | None = None,
        method: str = "euler forward",
        sample_time: float | None = None,
    ):
        super().__init__(name, sample_time)

        self.method = method.lower()
        if self.method not in ("euler forward", "euler backward"):
            raise ValueError(
                f"[{self.name}] Unsupported method '{method}'. "
                f"Allowed: 'euler forward', 'euler backward'."
            )

        # direct feedthrough policy
        self.direct_feedthrough = (self.method == "euler backward")

        # ports
        self.inputs["in"] = None
        self.outputs["out"] = None

        # shape policy
        self._resolved_shape: tuple[int, int] | None = None

        # state
        self.state["x"] = None
        self.next_state["x"] = None

        # Placeholder initialization (never None)
        self._placeholder = np.zeros((1, 1), dtype=float)

        self._initial_state_raw: np.ndarray | None = None
        if initial_state is not None:
            x0 = self._to_2d_array("initial_state", initial_state).astype(float)
            self._initial_state_raw = x0.copy()

            # If non-scalar: freeze immediately. If scalar (1,1): keep unfrozen placeholder semantics.
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
        # Never propagate None: guarantee placeholders even when no initial_state.
        if self._initial_state_raw is not None:
            x0 = self._initial_state_raw.copy()

            # If initial_state is non-scalar, freeze is already set in __init__.
            # If scalar, keep unresolved unless later a non-scalar input appears.
            self.state["x"] = x0.copy()
            self.next_state["x"] = x0.copy()

            # output at init:
            # forward -> y=x
            # backward -> y=x + dt*u, but u may be unknown at init; we take u=0 (consistent with "no None")
            if self.method == "euler forward":
                self.outputs["out"] = x0.copy()
            else:
                self.outputs["out"] = x0.copy()

        else:
            self.state["x"] = self._placeholder.copy()
            self.next_state["x"] = self._placeholder.copy()
            self.outputs["out"] = self._placeholder.copy()

    # ------------------------------------------------------------------
    def output_update(self, t: float, dt: float) -> None:
        x = self._normalize_state()

        if self.method == "euler forward":
            self.outputs["out"] = x.copy()
            return

        # euler backward: y = x + dt*u
        u = self._normalize_input(self.inputs["in"])
        self.outputs["out"] = x + dt * u

    # ------------------------------------------------------------------
    def state_update(self, t: float, dt: float) -> None:
        # Even if input is not available due to execution order, do not crash:
        # treat missing as zeros (same idea: "0 if not defined").
        u = self._normalize_input(self.inputs["in"])

        x = self._normalize_state()

        # ensure x matches u when shape resolved by u
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
        """
        Freeze shape if:
            - shape not resolved yet
            - and u is non-scalar (shape != (1,1))
        """
        if u.ndim != 2:
            raise ValueError(
                f"[{self.name}] Input 'in' must be a 2D array. Got ndim={u.ndim} with shape {u.shape}."
            )

        if self._resolved_shape is None and u.shape != (1, 1):
            self._resolved_shape = u.shape

            # Upgrade state/output from placeholder scalar -> matrix if needed
            if self.state["x"] is None:
                self.state["x"] = np.zeros(self._resolved_shape, dtype=float)
            else:
                x = np.asarray(self.state["x"], dtype=float)
                if x.shape == (1, 1):
                    scalar = float(x[0, 0])
                    self.state["x"] = np.full(self._resolved_shape, scalar, dtype=float)

            # keep next_state consistent
            self.next_state["x"] = np.asarray(self.state["x"], dtype=float).copy()

            y = np.asarray(self.outputs["out"], dtype=float)
            if y.shape == (1, 1):
                scalar = float(y[0, 0])
                self.outputs["out"] = np.full(self._resolved_shape, scalar, dtype=float)

    # ------------------------------------------------------------------
    def _normalize_input(self, u: ArrayLike | None) -> np.ndarray:
        """
        Normalize input to 2D array, apply shape policy and scalar broadcasting.

        If u is None:
            - return zeros of resolved shape if known,
            - else return (1,1) zeros (placeholder), without freezing.
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

        # Potentially freeze shape when a non-scalar appears
        self._maybe_freeze_shape_from(u_arr)

        # If shape is frozen and input is scalar -> broadcast
        if self._resolved_shape is not None:
            if u_arr.shape == (1, 1) and self._resolved_shape != (1, 1):
                return np.full(self._resolved_shape, float(u_arr[0, 0]), dtype=float)

            if u_arr.shape != self._resolved_shape:
                raise ValueError(
                    f"[{self.name}] Input 'in' shape changed: expected {self._resolved_shape}, got {u_arr.shape}."
                )

        return u_arr

    # ------------------------------------------------------------------
    def _normalize_state(self) -> np.ndarray:
        """
        Ensure state exists and matches resolved shape.
        """
        x = np.asarray(self.state["x"], dtype=float)

        # If shape resolved and x is scalar placeholder -> broadcast
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
