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


class Ramp(BlockSource):
    """Multi-dimensional ramp signal source block.

    Generates a ramp signal element-wise on a 2D output array:

        y(t) = offset + slope * max(0, t - start_time)

    Parameters may be scalars, vectors, or matrices. Only scalar-to-shape
    broadcasting is allowed; all non-scalar parameters must share the same
    shape.

    Attributes:
        slope: Ramp slope as a 2D array.
        start_time: Time at which the ramp starts, as a 2D array.
        offset: Output value before the ramp starts, as a 2D array.
    """

    def __init__(
        self,
        name: str,
        slope: ArrayLike,
        start_time: ArrayLike = 0.0,
        offset: ArrayLike | None = None,
        sample_time: float | None = None,
    ):
        """Initialize a Ramp block.

        Args:
            name: Unique identifier for this block instance.
            slope: Ramp slope. Can be scalar, vector, or matrix.
            start_time: Time at which the ramp starts in seconds. Can be
                scalar, vector, or matrix.
            offset: Output value before the ramp starts. Defaults to zero.
                Can be scalar, vector, or matrix.
            sample_time: Sampling period in seconds, or None to use the
                global simulation dt.

        Raises:
            ValueError: If non-scalar parameters have incompatible shapes.
        """
        super().__init__(name, sample_time)

        S = self._to_2d_array("slope", slope, dtype=float)
        T = self._to_2d_array("start_time", start_time, dtype=float)

        if offset is None:
            O = np.array([[0.0]], dtype=float)  # scalar, will be broadcast if needed
        else:
            O = self._to_2d_array("offset", offset, dtype=float)

        target_shape = self._resolve_common_shape({"slope": S, "start_time": T, "offset": O})

        self.slope = self._broadcast_scalar_only("slope", S, target_shape)
        self.start_time = self._broadcast_scalar_only("start_time", T, target_shape)
        self.offset = self._broadcast_scalar_only("offset", O, target_shape)

        self.outputs["out"] = self.offset.copy()


    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------

    def initialize(self, t0: float) -> None:
        """Set the output to the offset value at t0.

        Args:
            t0: Initial simulation time in seconds.
        """
        self.outputs["out"] = self.offset.copy()

    def output_update(self, t: float, dt: float) -> None:
        """Compute and write the ramp value to the output port.

        Args:
            t: Current simulation time in seconds.
            dt: Current time step in seconds.
        """
        dt_mat = np.maximum(0.0, t - self.start_time)
        self.outputs["out"] = self.offset + self.slope * dt_mat
