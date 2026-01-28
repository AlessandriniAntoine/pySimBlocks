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


class StateFeedback(Block):
    """
    Discrete-time state-feedback controller block.

    Summary:
        Implements a static discrete-time state-feedback control law:
            u = G @ r - K @ x

    Parameters:
        K : array-like, shape (m, n)
            State feedback gain matrix.
        G : array-like, shape (m, p)
            Reference feedforward gain matrix.
        sample_time : float, optional
            Block execution period.

    Inputs:
        r : array (p, 1)
            Reference vector.
        x : array (n, 1)
            State vector.

    Outputs:
        u : array (m, 1)
            Control vector.

    Notes:
        - Stateless block.
        - This block intentionally enforces column-vector inputs.
        - No implicit flattening is performed.
    """

    direct_feedthrough = True

    def __init__(self, name: str, K, G, sample_time: float | None = None):
        super().__init__(name, sample_time)

        self.K = np.asarray(K, dtype=float)
        self.G = np.asarray(G, dtype=float)

        if self.K.ndim != 2:
            raise ValueError(f"[{self.name}] K must be a 2D array (m,n). Got shape {self.K.shape}.")
        if self.G.ndim != 2:
            raise ValueError(f"[{self.name}] G must be a 2D array (m,p). Got shape {self.G.shape}.")

        m, n = self.K.shape
        m2, p = self.G.shape

        if m != m2:
            raise ValueError(
                f"[{self.name}] Inconsistent dimensions: "
                f"K is {self.K.shape} while G is {self.G.shape} (first dimension must match)."
            )

        # cached expected sizes for input validation
        self._m = m
        self._n = n
        self._p = p

        # Ports
        self.inputs["r"] = None
        self.inputs["x"] = None
        self.outputs["u"] = None

        # freeze input shapes once seen (optional but consistent)
        self._input_shapes = {}

    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------
    def initialize(self, t0: float):
        r = self.inputs["r"]
        x = self.inputs["x"]
        if r is None or x is None:
            self.outputs["u"] = None
            return

        r = self._require_col_vector("r", self._p)
        x = self._require_col_vector("x", self._n)

        self.outputs["u"] = self.G @ r - self.K @ x

    # ------------------------------------------------------------------
    def output_update(self, t: float, dt: float):
        r = self._require_col_vector("r", self._p)
        x = self._require_col_vector("x", self._n)

        self.outputs["u"] = self.G @ r - self.K @ x

    # ------------------------------------------------------------------
    def state_update(self, t: float, dt: float):
        pass


    # --------------------------------------------------------------------------
    # Private methods
    # --------------------------------------------------------------------------
    def _require_col_vector(self, port: str, expected_rows: int) -> np.ndarray:
        u = self.inputs[port]
        if u is None:
            raise RuntimeError(f"[{self.name}] Input '{port}' is not connected or not set.")

        arr = np.asarray(u, dtype=float)

        if arr.ndim != 2 or arr.shape[1] != 1:
            raise ValueError(
                f"[{self.name}] Input '{port}' must be a column vector (n,1). Got shape {arr.shape}."
            )

        if arr.shape[0] != expected_rows:
            raise ValueError(
                f"[{self.name}] Input '{port}' has wrong dimension: expected ({expected_rows},1), got {arr.shape}."
            )

        return arr


