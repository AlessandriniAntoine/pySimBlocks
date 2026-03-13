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

import numpy as np
from pySimBlocks.core.block import Block


class StateFeedback(Block):
    """Discrete-time state-feedback controller block.

    Implements a static discrete-time state-feedback control law:
        u = G @ r - K @ x

    Both inputs must be column vectors. No implicit flattening is performed.

    Attributes:
        K: State feedback gain matrix of shape (m, n).
        G: Reference feedforward gain matrix of shape (m, p).
    """

    direct_feedthrough = True

    def __init__(self, name: str, K, G, sample_time: float | None = None):
        """Initialize a StateFeedback block.

        Args:
            name: Unique identifier for this block instance.
            K: State feedback gain matrix, array-like of shape (m, n).
            G: Reference feedforward gain matrix, array-like of shape (m, p).
            sample_time: Sampling period in seconds, or None to use the
                global simulation dt.

        Raises:
            ValueError: If K or G are not 2D, or if their first dimensions
                do not match.
        """
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

        self._m = m
        self._n = n
        self._p = p

        self.inputs["r"] = None
        self.inputs["x"] = None
        self.outputs["u"] = None

        self._input_shapes = {}


    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------

    def initialize(self, t0: float) -> None:
        """Set the output to zero, or compute u if inputs are already available.

        Args:
            t0: Initial simulation time in seconds.
        """
        r = self.inputs["r"]
        x = self.inputs["x"]
        if r is None or x is None:
            self.outputs["u"] = np.zeros((self._m, 1))
            return

        try:
            r = self._require_col_vector("r", self._p)
            x = self._require_col_vector("x", self._n)
            self.outputs["u"] = self.G @ r - self.K @ x
        except Exception as _:
            self.outputs["u"] = np.zeros((self._m, 1))

    def output_update(self, t: float, dt: float) -> None:
        """Compute the control output u = G @ r - K @ x.

        Args:
            t: Current simulation time in seconds.
            dt: Current time step in seconds.

        Raises:
            RuntimeError: If input ``r`` or ``x`` is not connected.
            ValueError: If input shapes do not match the gain matrices.
        """
        r = self._require_col_vector("r", self._p)
        x = self._require_col_vector("x", self._n)

        self.outputs["u"] = self.G @ r - self.K @ x

    def state_update(self, t: float, dt: float) -> None:
        """No-op: StateFeedback carries no internal state."""


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
            ValueError: If the array is not a column vector or has the
                wrong number of rows.
        """
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
