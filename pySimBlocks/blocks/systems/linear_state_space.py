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


class LinearStateSpace(Block):
    """Discrete-time linear state-space system block.

    Implements a strictly proper discrete-time linear system:

        x[k+1] = A x[k] + B u[k]
         
        y[k]   = C x[k]

    The D matrix is intentionally not supported to avoid algebraic loops.

    Attributes:
        A: State transition matrix of shape (n, n).
        B: Input matrix of shape (n, m).
        C: Output matrix of shape (p, n).
    """

    direct_feedthrough = False

    def __init__(
        self,
        name: str,
        A: ArrayLike,
        B: ArrayLike,
        C: ArrayLike,
        x0: ArrayLike | None = None,
        sample_time: float | None = None,
    ):
        """Initialize a LinearStateSpace block.

        Args:
            name: Unique identifier for this block instance.
            A: State transition matrix, array-like of shape (n, n).
            B: Input matrix, array-like of shape (n, m).
            C: Output matrix, array-like of shape (p, n).
            x0: Initial state vector, array-like of shape (n, 1) or (n,).
                Defaults to zeros.
            sample_time: Sampling period in seconds, or None to use the
                global simulation dt.

        Raises:
            ValueError: If any matrix is not 2D, if dimensions are
                inconsistent, or if x0 does not match the state dimension.
        """
        super().__init__(name, sample_time)

        self.A = np.asarray(A, dtype=float)
        self.B = np.asarray(B, dtype=float)
        self.C = np.asarray(C, dtype=float)

        if self.A.ndim != 2:
            raise ValueError(f"[{self.name}] A must be 2D. Got shape {self.A.shape}.")
        if self.B.ndim != 2:
            raise ValueError(f"[{self.name}] B must be 2D. Got shape {self.B.shape}.")
        if self.C.ndim != 2:
            raise ValueError(f"[{self.name}] C must be 2D. Got shape {self.C.shape}.")

        n = self.A.shape[0]
        if self.A.shape != (n, n):
            raise ValueError(f"[{self.name}] A must be square (n,n). Got {self.A.shape}.")

        if self.B.shape[0] != n:
            raise ValueError(
                f"[{self.name}] B must have n rows. A is {self.A.shape}, B is {self.B.shape}."
            )

        if self.C.shape[1] != n:
            raise ValueError(
                f"[{self.name}] C must have n columns. A is {self.A.shape}, C is {self.C.shape}."
            )

        self._n = n
        self._m = self.B.shape[1]
        self._p = self.C.shape[0]

        if x0 is None:
            x0_arr = np.zeros((n, 1), dtype=float)
        else:
            x0_arr = np.asarray(x0, dtype=float)
            if x0_arr.ndim == 0:
                x0_arr = x0_arr.reshape(1, 1)
            elif x0_arr.ndim == 1:
                x0_arr = x0_arr.reshape(-1, 1)
            elif x0_arr.ndim == 2:
                pass
            else:
                raise ValueError(f"[{self.name}] x0 must be 1D or 2D. Got shape {x0_arr.shape}.")

            if x0_arr.shape != (n, 1):
                raise ValueError(f"[{self.name}] x0 must have shape ({n}, 1). Got {x0_arr.shape}.")

        self.state["x"] = x0_arr.copy()
        self.next_state["x"] = x0_arr.copy()

        self.inputs["u"] = None
        self.outputs["y"] = None
        self.outputs["x"] = None


    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------

    def initialize(self, t0: float) -> None:
        """Compute initial outputs from the initial state.

        Args:
            t0: Initial simulation time in seconds.
        """
        x = self.state["x"]
        self.outputs["y"] = self.C @ x
        self.outputs["x"] = x.copy()
        self.next_state["x"] = x.copy()

    def output_update(self, t: float, dt: float) -> None:
        """Compute y and x outputs from the committed state.

        Args:
            t: Current simulation time in seconds.
            dt: Current time step in seconds.
        """
        x = self.state["x"]
        self.outputs["y"] = self.C @ x
        self.outputs["x"] = x.copy()

    def state_update(self, t: float, dt: float) -> None:
        """Compute the next state x[k+1] = A x[k] + B u[k].

        Args:
            t: Current simulation time in seconds.
            dt: Current time step in seconds.

        Raises:
            RuntimeError: If input ``u`` is not connected.
            ValueError: If input ``u`` has the wrong shape.
        """
        u = self.inputs["u"]
        if u is None:
            raise RuntimeError(f"[{self.name}] Input 'u' is not connected or not set.")

        u_vec = self._to_col_vec("u", u, self._m)
        x = self.state["x"]

        self.next_state["x"] = self.A @ x + self.B @ u_vec


    # --------------------------------------------------------------------------
    # Private methods
    # --------------------------------------------------------------------------

    def _to_col_vec(self, name: str, value: ArrayLike, expected_rows: int) -> np.ndarray:
        """Normalize value to a (n,1) column vector and validate its size."""
        arr = np.asarray(value, dtype=float)

        if arr.ndim == 0:
            arr = arr.reshape(1, 1)
        elif arr.ndim == 1:
            arr = arr.reshape(-1, 1)
        elif arr.ndim == 2:
            pass
        else:
            raise ValueError(f"[{self.name}] {name} must be 1D or 2D. Got shape {arr.shape}.")

        if arr.shape[1] != 1:
            raise ValueError(f"[{self.name}] {name} must be a column vector (k,1). Got {arr.shape}.")

        if arr.shape[0] != expected_rows:
            raise ValueError(
                f"[{self.name}] {name} must have shape ({expected_rows},1). Got {arr.shape}."
            )

        return arr
