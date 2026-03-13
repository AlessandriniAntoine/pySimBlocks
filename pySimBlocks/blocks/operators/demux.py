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


class Demux(Block):
    """Vector split block (inverse of Mux).

    Splits one input column vector of length n into p output segments. Segment
    sizes are distributed as evenly as possible: let q = n // p and m = n % p,
    then the first m outputs have size q+1 and the remaining p-m outputs have
    size q.

    Attributes:
        num_outputs: Number of output segments to produce.
    """

    direct_feedthrough = True

    def __init__(self, name: str, num_outputs: int = 2, sample_time: float | None = None):
        """Initialize a Demux block.

        Args:
            name: Unique identifier for this block instance.
            num_outputs: Number of output segments. Must be >= 1.
            sample_time: Sampling period in seconds, or None to use the global
                simulation dt.

        Raises:
            ValueError: If ``num_outputs`` is not a positive integer.
        """
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
        """Compute initial outputs, or set zero placeholders if input is unavailable.

        Args:
            t0: Initial simulation time in seconds.
        """
        if self.inputs["in"] is None:
            for i in range(self.num_outputs):
                self.outputs[f"out{i+1}"] = np.zeros((1, 1), dtype=float)
            return

        self._compute_outputs()

    def output_update(self, t: float, dt: float) -> None:
        """Split the input vector and write the segments to the output ports.

        Args:
            t: Current simulation time in seconds.
            dt: Current time step in seconds.

        Raises:
            RuntimeError: If input ``'in'`` is not connected.
            ValueError: If input is not a column vector or has fewer elements
                than ``num_outputs``.
        """
        self._compute_outputs()

    def state_update(self, t: float, dt: float) -> None:
        """No-op: Demux is a stateless block.

        Args:
            t: Current simulation time in seconds.
            dt: Current time step in seconds.
        """
        return


    # --------------------------------------------------------------------------
    # Private methods
    # --------------------------------------------------------------------------

    def _to_vector(self, value: ArrayLike) -> np.ndarray:
        """Validate and return the input as a (n,1) column vector."""
        arr = np.asarray(value, dtype=float)

        if arr.ndim != 2 or arr.shape[1] != 1:
            raise ValueError(
                f"[{self.name}] Input 'in' must be a column vector (n,1). "
                f"Got shape {arr.shape}."
            )
        return arr

    def _compute_outputs(self) -> None:
        """Split the input vector into output segments."""
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
