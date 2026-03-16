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


class PolytopicStateSpace(Block):
    """Discrete-time polytopic state-space block.

    Implements a convex combination of linear state-space models:

        x[k+1] = sum_{i=1}^r w_i[k] (A_i x[k] + B_i u[k])

        y[k]   = C x[k]

    The weight vector ``w`` must be non-negative and sum to 1 at each step.
    Matrices A and B are provided as horizontal concatenations of the
    per-vertex matrices: A = [A_1, ..., A_r] of shape (nx, r*nx) and
    B = [B_1, ..., B_r] of shape (nx, r*nu).

    Attributes:
        A: Concatenated vertex state matrices of shape (nx, r*nx).
        B: Concatenated vertex input matrices of shape (nx, r*nu).
        C: Output matrix of shape (ny, nx).
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
        """Initialize a PolytopicStateSpace block.

        Args:
            name: Unique identifier for this block instance.
            A: Concatenated vertex state matrices [A_1, ..., A_r],
                array-like of shape (nx, r*nx).
            B: Concatenated vertex input matrices [B_1, ..., B_r],
                array-like of shape (nx, r*nu).
            C: Output matrix, array-like of shape (ny, nx).
            x0: Initial state vector, array-like of shape (nx, 1) or (nx,).
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

        nx = self.A.shape[0]
        if nx <= 0:
            raise ValueError(f"[{self.name}] A must have at least one row.")
        if self.A.shape[1] % nx != 0:
            raise ValueError(
                f"[{self.name}] A must have shape (nx, r*nx). Got {self.A.shape}."
            )

        r = self.A.shape[1] // nx
        if r <= 0:
            raise ValueError(f"[{self.name}] Number of vertices r must be >= 1.")

        if self.B.shape[0] != nx:
            raise ValueError(
                f"[{self.name}] B must have nx rows. A is {self.A.shape}, B is {self.B.shape}."
            )
        if self.B.shape[1] % r != 0:
            raise ValueError(
                f"[{self.name}] B must have shape (nx, r*nu). A gives r={r}, B is {self.B.shape}."
            )

        nu = self.B.shape[1] // r
        if nu <= 0:
            raise ValueError(f"[{self.name}] Input size nu must be >= 1.")

        if self.C.shape[1] != nx:
            raise ValueError(
                f"[{self.name}] C must have nx columns. A is {self.A.shape}, C is {self.C.shape}."
            )

        ny = self.C.shape[0]

        self._nx = nx
        self._nu = nu
        self._ny = ny
        self._r = r

        if x0 is None:
            x0_arr = np.zeros((nx, 1), dtype=float)
        else:
            x0_arr = self._to_col_vec("x0", x0, nx)

        self.state["x"] = x0_arr.copy()
        self.next_state["x"] = x0_arr.copy()

        self.inputs["w"] = None
        self.inputs["u"] = None
        self.outputs["x"] = None
        self.outputs["y"] = None


    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------

    def initialize(self, t0: float) -> None:
        """Compute initial outputs from the initial state.

        Args:
            t0: Initial simulation time in seconds.
        """
        x = self.state["x"]
        self.outputs["x"] = x.copy()
        self.outputs["y"] = self.C @ x
        self.next_state["x"] = x.copy()

    def output_update(self, t: float, dt: float) -> None:
        """Compute y and x outputs from the committed state.

        Args:
            t: Current simulation time in seconds.
            dt: Current time step in seconds.
        """
        x = self.state["x"]
        self.outputs["x"] = x.copy()
        self.outputs["y"] = self.C @ x

    def state_update(self, t: float, dt: float) -> None:
        """Compute the next state as a weighted sum of vertex dynamics.

        Args:
            t: Current simulation time in seconds.
            dt: Current time step in seconds.

        Raises:
            RuntimeError: If inputs ``w`` or ``u`` are not connected.
            ValueError: If ``w`` does not sum to 1, has negative entries,
                or if input shapes are wrong.
        """
        w = self.inputs["w"]
        u = self.inputs["u"]
        if w is None:
            raise RuntimeError(f"[{self.name}] Input 'w' is not connected or not set.")
        if u is None:
            raise RuntimeError(f"[{self.name}] Input 'u' is not connected or not set.")

        w_vec = self._to_col_vec("w", w, self._r)
        if not np.isclose(np.sum(w_vec), 1.0):
            raise ValueError(f"[{self.name}] Vertex weights w must sum to 1. Got sum {np.sum(w_vec)}.")
        if np.any(w_vec < 0):
            raise ValueError(f"[{self.name}] Vertex weights w must be non-negative. Got {w_vec.flatten()}.")

        u_vec = self._to_col_vec("u", u, self._nu)
        x = self.state["x"]

        x_next = self.A @ np.kron(w_vec, x) + self.B @ np.kron(w_vec, u_vec)
        self.next_state["x"] = x_next


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
