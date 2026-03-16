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


class Mux(Block):
    """Vertical signal concatenation block.

    Concatenates multiple scalar or column-vector inputs vertically into a
    single output column vector. Each input must be a scalar, a 1D array, or
    a column vector (n,1). Any 2D non-column input (k,m) with m != 1 is
    rejected.

    Attributes:
        num_inputs: Number of input ports to concatenate.
    """

    direct_feedthrough = True

    def __init__(self, name: str, num_inputs: int = 2, sample_time: float | None = None):
        """Initialize a Mux block.

        Args:
            name: Unique identifier for this block instance.
            num_inputs: Number of input ports to concatenate. Must be >= 1.
            sample_time: Sampling period in seconds, or None to use the global
                simulation dt.

        Raises:
            ValueError: If ``num_inputs`` is not a positive integer.
        """
        super().__init__(name, sample_time)

        if not isinstance(num_inputs, int) or num_inputs < 1:
            raise ValueError(f"[{self.name}] num_inputs must be a positive integer.")
        self.num_inputs = num_inputs

        for i in range(num_inputs):
            self.inputs[f"in{i+1}"] = None

        self.outputs["out"] = None


    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------

    def initialize(self, t0: float) -> None:
        """Compute the initial output if all inputs are available.

        Args:
            t0: Initial simulation time in seconds.
        """
        for i in range(self.num_inputs):
            if self.inputs[f"in{i+1}"] is None:
                self.outputs["out"] = None
                return

        self.outputs["out"] = self._compute_output()

    def output_update(self, t: float, dt: float) -> None:
        """Concatenate all inputs vertically and write the result to the output port.

        Args:
            t: Current simulation time in seconds.
            dt: Current time step in seconds.

        Raises:
            RuntimeError: If any input port is not connected.
            ValueError: If any input is not a scalar, 1D, or column vector.
        """
        self.outputs["out"] = self._compute_output()

    def state_update(self, t: float, dt: float) -> None:
        """No-op: Mux is a stateless block.

        Args:
            t: Current simulation time in seconds.
            dt: Current time step in seconds.
        """
        return


    # --------------------------------------------------------------------------
    # Private methods
    # --------------------------------------------------------------------------

    def _to_column_vector(self, input_name: str, value: ArrayLike) -> np.ndarray:
        """Convert a scalar, 1D array, or column vector to a (n,1) array."""
        arr = np.asarray(value, dtype=float)

        if arr.ndim == 0:
            return arr.reshape(1, 1)
        if arr.ndim == 1:
            return arr.reshape(-1, 1)
        if arr.ndim == 2:
            if arr.shape[1] != 1:
                raise ValueError(
                    f"[{self.name}] Input '{input_name}' must be a column vector (n,1). "
                    f"Got shape {arr.shape}."
                )
            return arr

        raise ValueError(
            f"[{self.name}] Input '{input_name}' must be scalar, 1D, or a column vector (n,1). "
            f"Got ndim={arr.ndim} with shape {arr.shape}."
        )

    def _compute_output(self) -> np.ndarray:
        """Collect and concatenate all input column vectors."""
        vectors = []

        for i in range(self.num_inputs):
            key = f"in{i+1}"
            u = self.inputs[key]
            if u is None:
                raise RuntimeError(f"[{self.name}] Input '{key}' is not connected or not set.")

            vectors.append(self._to_column_vector(key, u))

        return np.vstack(vectors)
