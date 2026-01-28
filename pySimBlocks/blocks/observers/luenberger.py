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
from pySimBlocks.core.block import Block


class Luenberger(Block):
    """
    Discrete-time Luenberger state observer block.

    Summary:
        Estimates the state using:
            y_hat[k] = C x_hat[k]
            x_hat[k+1] = A x_hat[k] + B u[k] + L (y[k] - y_hat[k])

    Parameters:
        A : array-like, shape (n, n)
        B : array-like, shape (n, m)
        C : array-like, shape (p, n)
        L : array-like, shape (n, p)
        x0 : array-like, shape (n, 1), optional
        sample_time : float, optional

    Inputs:
        u : array (m, 1)
        y : array (p, 1)

    Outputs:
        x_hat : array (n, 1)
        y_hat : array (p, 1)

    Notes:
        - Stateful block.
        - No direct feedthrough.
        - D matrix intentionally not supported.
        - Input shapes are frozen once first seen.
    """

    direct_feedthrough = False

    def __init__(
        self,
        name: str,
        A,
        B,
        C,
        L,
        x0=None,
        sample_time: float | None = None,
    ):
        super().__init__(name, sample_time)

        # --- Matrices: strict 2D
        self.A = np.asarray(A, dtype=float)
        self.B = np.asarray(B, dtype=float)
        self.C = np.asarray(C, dtype=float)
        self.L = np.asarray(L, dtype=float)

        for M_name, M in (("A", self.A), ("B", self.B), ("C", self.C), ("L", self.L)):
            if M.ndim != 2:
                raise ValueError(f"[{self.name}] {M_name} must be a 2D array. Got shape {M.shape}.")

        n = self.A.shape[0]
        if self.A.shape[1] != n:
            raise ValueError(f"[{self.name}] A must be square (n,n). Got {self.A.shape}.")

        if self.B.shape[0] != n:
            raise ValueError(f"[{self.name}] B must have n rows to match A. Got B={self.B.shape}, A={self.A.shape}.")

        if self.C.shape[1] != n:
            raise ValueError(f"[{self.name}] C must have n columns to match A. Got C={self.C.shape}, A={self.A.shape}.")

        p = self.C.shape[0]
        m = self.B.shape[1]

        if self.L.shape != (n, p):
            raise ValueError(f"[{self.name}] L must have shape (n,p) = ({n},{p}). Got {self.L.shape}.")

        self._n = n
        self._m = m
        self._p = p

        # --- Initial state x0: strict (n,1), no flatten
        if x0 is None:
            x0_arr = np.zeros((n, 1), dtype=float)
        else:
            x0_arr = np.asarray(x0, dtype=float)
            if x0_arr.ndim != 2 or x0_arr.shape != (n, 1):
                raise ValueError(f"[{self.name}] x0 must have shape ({n},1). Got {x0_arr.shape}.")

        self.state["x_hat"] = x0_arr.copy()
        self.next_state["x_hat"] = x0_arr.copy()

        # --- Ports
        self.inputs["u"] = None
        self.inputs["y"] = None
        self.outputs["y_hat"] = None
        self.outputs["x_hat"] = None

        # Freeze input shapes once first seen
        self._input_shapes = {}


    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------
    def initialize(self, t0: float) -> None:
        x_hat = self.state["x_hat"]
        self.outputs["x_hat"] = x_hat.copy()
        self.outputs["y_hat"] = self.C @ x_hat
        self.next_state["x_hat"] = x_hat.copy()

    # ------------------------------------------------------------------
    def output_update(self, t: float, dt: float) -> None:
        x_hat = self.state["x_hat"]
        self.outputs["x_hat"] = x_hat.copy()
        self.outputs["y_hat"] = self.C @ x_hat

    # ------------------------------------------------------------------
    def state_update(self, t: float, dt: float) -> None:
        u = self._require_col_vector("u", self._m)
        y = self._require_col_vector("y", self._p)

        x_hat = self.state["x_hat"]
        y_hat = self.C @ x_hat

        self.next_state["x_hat"] = self.A @ x_hat + self.B @ u + self.L @ (y - y_hat)


    # --------------------------------------------------------------------------
    # Private methods
    # --------------------------------------------------------------------------
    def _require_col_vector(self, port: str, expected_rows: int) -> np.ndarray:
        val = self.inputs[port]
        if val is None:
            raise RuntimeError(f"[{self.name}] Input '{port}' is not connected or not set.")

        arr = np.asarray(val, dtype=float)

        # Strict: column vector only (no implicit flatten)
        if arr.ndim != 2 or arr.shape[1] != 1:
            raise ValueError(f"[{self.name}] Input '{port}' must be a column vector (n,1). Got {arr.shape}.")

        if arr.shape[0] != expected_rows:
            raise ValueError(
                f"[{self.name}] Input '{port}' has wrong dimension: expected ({expected_rows},1), got {arr.shape}."
            )

        # Freeze shape
        if port not in self._input_shapes:
            self._input_shapes[port] = arr.shape
        elif arr.shape != self._input_shapes[port]:
            raise ValueError(
                f"[{self.name}] Input '{port}' shape changed: expected {self._input_shapes[port]}, got {arr.shape}."
            )

        return arr


