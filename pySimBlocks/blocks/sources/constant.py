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
from pySimBlocks.core.block_source import BlockSource


class Constant(BlockSource):
    """
    Constant signal source block.

    Summary:
        Generates a constant output signal with a fixed value over time.
        The output does not depend on time or any input signal.

    Parameters (overview):
        value : float or array-like
            Constant output value. Can be scalar, vector, or matrix.
        sample_time : float, optional
            Block execution period.

    I/O:
        Inputs:
            (none)
        Outputs:
            out : constant output signal.

    Notes:
        - The block has no internal state.
        - The output value is held constant for the entire simulation.
        - Scalar values are normalized to shape (1,1).
        - 1D values are normalized to column vectors (n,1).
        - 2D values are preserved as matrices (m,n).
    """

    def __init__(
        self,
        name: str,
        value: ArrayLike = 1.0,
        sample_time: float | None = None,
    ):
        super().__init__(name, sample_time)

        # Accept numeric scalars and array-like
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
        self.outputs["out"] = self.value.copy()

    # ------------------------------------------------------------------
    def output_update(self, t: float, dt: float) -> None:
        self.outputs["out"] = self.value.copy()
