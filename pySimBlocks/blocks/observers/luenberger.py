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


class Luenberger(Block):
    """Discrete-time Luenberger state observer block.

    Estimates the state of a linear system using the correction law:

        y_hat[k]   = C x_hat[k]

        x_hat[k+1] = A x_hat[k] + B u[k] + L (y[k] - y_hat[k])

    The D matrix is intentionally not supported. Input column-vector shapes
    are frozen after the first call and must remain constant.

    Attributes:
        A: State transition matrix of shape (n, n).
        B: Input matrix of shape (n, m).
        C: Output matrix of shape (p, n).
        L: Observer gain matrix of shape (n, p).
    """

    direct_feedthrough = False

    def __init__(
        self,
        name: str,
        A: ArrayLike,
        B: ArrayLike,
        C: ArrayLike,
        L: ArrayLike,
        x0: ArrayLike | None = None,
        sample_time: float | None = None,
    ):
        """Initialize a Luenberger observer block.

        Args:
            name: Unique identifier for this block instance.
            A: State transition matrix, array-like of shape (n, n).
            B: Input matrix, array-like of shape (n, m).
            C: Output matrix, array-like of shape (p, n).
            L: Observer gain matrix, array-like of shape (n, p).
            x0: Initial state estimate, array-like of shape (n, 1).
                Defaults to zeros.
            sample_time: Sampling period in seconds, or None to use the
                global simulation dt.

        Raises:
            ValueError: If any matrix is not 2D, if dimensions are
                inconsistent, or if x0 does not have shape (n, 1).
        """
        super().__init__(name, sample_time)

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

        if x0 is None:
            x0_arr = np.zeros((n, 1), dtype=float)
        else:
            x0_arr = np.asarray(x0, dtype=float)
            if x0_arr.ndim != 2 or x0_arr.shape != (n, 1):
                raise ValueError(f"[{self.name}] x0 must have shape ({n},1). Got {x0_arr.shape}.")

        self.state["x_hat"] = x0_arr.copy()
        self.next_state["x_hat"] = x0_arr.copy()

        self.inputs["u"] = None
        self.inputs["y"] = None
        self.outputs["y_hat"] = None
        self.outputs["x_hat"] = None

        self._input_shapes = {}


    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------

    def initialize(self, t0: float) -> None:
        """Set initial outputs from the initial state estimate.

        Args:
            t0: Initial simulation time in seconds.
        """
        x_hat = self.state["x_hat"]
        self.outputs["x_hat"] = x_hat.copy()
        self.outputs["y_hat"] = self.C @ x_hat
        self.next_state["x_hat"] = x_hat.copy()

    def output_update(self, t: float, dt: float) -> None:
        """Compute x_hat and y_hat outputs from the committed state.

        Args:
            t: Current simulation time in seconds.
            dt: Current time step in seconds.
        """
        x_hat = self.state["x_hat"]
        self.outputs["x_hat"] = x_hat.copy()
        self.outputs["y_hat"] = self.C @ x_hat

    def state_update(self, t: float, dt: float) -> None:
        """Update the state estimate using the observer correction law.

        Args:
            t: Current simulation time in seconds.
            dt: Current time step in seconds.

        Raises:
            RuntimeError: If inputs ``u`` or ``y`` are not connected.
            ValueError: If input shapes are incompatible or have changed.
        """
        u = self._require_col_vector("u", self._m)
        y = self._require_col_vector("y", self._p)

        x_hat = self.state["x_hat"]
        y_hat = self.C @ x_hat

        self.next_state["x_hat"] = self.A @ x_hat + self.B @ u + self.L @ (y - y_hat)


    # --------------------------------------------------------------------------
    # Private methods
    # --------------------------------------------------------------------------

    def _require_col_vector(self, port: str, expected_rows: int) -> np.ndarray:
        """Validate and return an input port value as a column vector.

        Args:
            port: Name of the input port to read.
            expected_rows: Expected number of rows in the column vector.

        Returns:
            The input value as a 2D (n, 1) float array.

        Raises:
            RuntimeError: If the port value is None.
            ValueError: If the array is not a column vector, has the wrong
                number of rows, or its shape has changed since the first call.
        """
        val = self.inputs[port]
        if val is None:
            raise RuntimeError(f"[{self.name}] Input '{port}' is not connected or not set.")

        arr = np.asarray(val, dtype=float)

        if arr.ndim != 2 or arr.shape[1] != 1:
            raise ValueError(f"[{self.name}] Input '{port}' must be a column vector (n,1). Got {arr.shape}.")

        if arr.shape[0] != expected_rows:
            raise ValueError(
                f"[{self.name}] Input '{port}' has wrong dimension: expected ({expected_rows},1), got {arr.shape}."
            )

        if port not in self._input_shapes:
            self._input_shapes[port] = arr.shape
        elif arr.shape != self._input_shapes[port]:
            raise ValueError(
                f"[{self.name}] Input '{port}' shape changed: expected {self._input_shapes[port]}, got {arr.shape}."
            )

        return arr
