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


class LinearStateSpace(Block):
    """
    Discrete-time linear state-space system block.

    Summary:
        Implements a discrete-time linear state-space system without direct
        feedthrough, defined by state and output equations.

    Parameters (overview):
        A : array-like
            State transition matrix.
        B : array-like
            Input matrix.
        C : array-like
            Output matrix.
        x0 : array-like, optional
            Initial state vector.
        sample_time : float, optional
            Block execution period.

    I/O:
        Inputs:
            u : input vector.
        Outputs:
            y : output vector.
            x : state vector.

    Notes:
        - The system is strictly proper (no direct feedthrough).
        - The block has internal state.
        - Matrix D is intentionally not supported to avoid algebraic loops.
        - The state is updated once per simulation step.
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
        super().__init__(name, sample_time)

        self.A = np.asarray(A, dtype=float)
        self.B = np.asarray(B, dtype=float)
        self.C = np.asarray(C, dtype=float)

        # --- basic matrix checks
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

        # --- initial state x0
        if x0 is None:
            x0_arr = np.zeros((n, 1), dtype=float)
        else:
            x0_arr = np.asarray(x0, dtype=float)
            if x0_arr.ndim == 0:
                # scalar x0 is not acceptable for n>1
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

        # ports
        self.inputs["u"] = None
        self.outputs["y"] = None
        self.outputs["x"] = None


    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------
    def initialize(self, t0: float) -> None:
        x = self.state["x"]
        self.outputs["y"] = self.C @ x
        self.outputs["x"] = x.copy()
        self.next_state["x"] = x.copy()

    # ------------------------------------------------------------------
    def output_update(self, t: float, dt: float) -> None:
        x = self.state["x"]
        self.outputs["y"] = self.C @ x
        self.outputs["x"] = x.copy()

    # ------------------------------------------------------------------
    def state_update(self, t: float, dt: float) -> None:
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
