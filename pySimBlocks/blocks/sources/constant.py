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
from pySimBlocks.core.block_source import BlockSource


class Constant(BlockSource):
    """Constant signal source block.

    Generates a constant output signal with a fixed value over time.
    The output does not depend on time or any input signal.

    Attributes:
        value: Constant output value as a 2D array. Scalars are normalized
            to shape (1,1), 1D arrays to column vectors (n,1), and 2D
            arrays are preserved as-is.
    """

    def __init__(
        self,
        name: str,
        value: ArrayLike = 1.0,
        sample_time: float | None = None,
    ):
        """Initialize a Constant block.

        Args:
            name: Unique identifier for this block instance.
            value: Constant output value. Can be scalar, vector, or matrix.
            sample_time: Sampling period in seconds, or None to use the
                global simulation dt.

        Raises:
            TypeError: If value is not numeric or array-like.
        """
        super().__init__(name, sample_time)

        if not isinstance(value, (list, tuple, np.ndarray, float, int)):
            raise TypeError(
                f"[{self.name}] Constant 'value' must be numeric or array-like."
            )

        arr = self._to_2d_array("value", value, dtype=float)

        self.value = arr
        self.outputs["out"] = arr.copy()


    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------

    def initialize(self, t0: float) -> None:
        """Set the output to the constant value at t0.

        Args:
            t0: Initial simulation time in seconds.
        """
        self.outputs["out"] = self.value.copy()

    def output_update(self, t: float, dt: float) -> None:
        """Write the constant value to the output port.

        Args:
            t: Current simulation time in seconds.
            dt: Current time step in seconds.
        """
        self.outputs["out"] = self.value.copy()
