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
from numpy.typing import ArrayLike

from pySimBlocks.core.block import Block


class Demux(Block):
    """
    Vector split block (inverse of Mux).

    Summary:
        Splits one input column vector into multiple output segments.

    Parameters:
        num_outputs : int
            Number of scalar outputs to produce.
        sample_time : float, optional
            Block execution period.

    Inputs:
        in : vector (n,1)
            Input must be a column vector.

    Outputs:
        out1, out2, ..., outP : array (k,1)
            Output segment sizes follow:
              - q = n // p
              - m = n % p
              - first m outputs have size (q+1,1)
              - remaining (p-m) outputs have size (q,1)
    """

    direct_feedthrough = True

    def __init__(self, name: str, num_outputs: int = 2, sample_time: float | None = None):
        super().__init__(name, sample_time)

        if not isinstance(num_outputs, int) or num_outputs < 1:
            raise ValueError(f"[{self.name}] num_outputs must be a positive integer.")
        self.num_outputs = num_outputs

        self.inputs["in"] = None
        for i in range(num_outputs):
            self.outputs[f"out{i+1}"] = None


    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------
    def initialize(self, t0: float) -> None:
        if self.inputs["in"] is None:
            for i in range(self.num_outputs):
                self.outputs[f"out{i+1}"] = np.zeros((1, 1), dtype=float)
            return

        self._compute_outputs()

    # ---------------------------------------------------------
    def output_update(self, t: float, dt: float) -> None:
        self._compute_outputs()

    # ---------------------------------------------------------
    def state_update(self, t: float, dt: float) -> None:
        return  # stateless


    # --------------------------------------------------------------------------
    # Private methods
    # --------------------------------------------------------------------------
    def _to_vector(self, value: ArrayLike) -> np.ndarray:
        arr = np.asarray(value, dtype=float)

        if arr.ndim != 2 or arr.shape[1] != 1:
            raise ValueError(
                f"[{self.name}] Input 'in' must be a column vector (n,1). "
                f"Got shape {arr.shape}."
            )
        return arr

    # ---------------------------------------------------------
    def _compute_outputs(self) -> None:
        u = self.inputs["in"]
        if u is None:
            raise RuntimeError(f"[{self.name}] Input 'in' is not connected or not set.")

        vec = self._to_vector(u)
        n = vec.shape[0]
        p = self.num_outputs

        if p > n:
            raise ValueError(
                f"[{self.name}] num_outputs ({p}) must be <= input vector length ({n})."
            )

        q = n // p
        m = n % p

        start = 0
        for i in range(p):
            seg_len = q + 1 if i < m else q
            end = start + seg_len
            self.outputs[f"out{i+1}"] = vec[start:end].copy()
            start = end
