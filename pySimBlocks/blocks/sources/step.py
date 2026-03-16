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

from numpy.typing import ArrayLike
from pySimBlocks.core.block_source import BlockSource


class Step(BlockSource):
    """Step signal source block.

    Generates a step signal that switches from an initial value to a final
    value at a specified time. Scalar values are broadcast to match the shape
    of non-scalar counterparts.

    Attributes:
        value_before: Output value before the step, as a 2D array.
        value_after: Output value after the step, as a 2D array.
        start_time: Time at which the step occurs in seconds.
        EPS: Tolerance used to compensate floating-point rounding on
            discrete time grids.
    """

    def __init__(
        self,
        name: str,
        value_before: ArrayLike = 0.0,
        value_after: ArrayLike = 1.0,
        start_time: float = 1.0,
        sample_time: float | None = None,
        eps: float = 1e-12,
    ):
        """Initialize a Step block.

        Args:
            name: Unique identifier for this block instance.
            value_before: Output value before the step. Can be scalar,
                vector, or matrix.
            value_after: Output value after the step. Can be scalar,
                vector, or matrix.
            start_time: Time at which the step occurs in seconds.
            sample_time: Sampling period in seconds, or None to use the
                global simulation dt.
            eps: Tolerance for floating-point comparison against start_time.

        Raises:
            TypeError: If start_time is not a float or int.
            ValueError: If value_before and value_after have incompatible
                non-scalar shapes.
        """
        super().__init__(name, sample_time)

        vb = self._to_2d_array("value_before", value_before, dtype=float)
        va = self._to_2d_array("value_after", value_after, dtype=float)

        shape = self._resolve_common_shape({"value_before": vb, "value_after": va})
        self.value_before = self._broadcast_scalar_only("value_before", vb, shape)
        self.value_after  = self._broadcast_scalar_only("value_after",  va, shape)

        if not isinstance(start_time, (float, int)):
            raise TypeError(f"[{self.name}] start_time must be a float or int.")
        self.start_time = float(start_time)

        self.outputs["out"] = None
        self.EPS = float(eps)


    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------

    def initialize(self, t0: float) -> None:
        """Set the output to value_before or value_after depending on t0.

        Args:
            t0: Initial simulation time in seconds.
        """
        self.outputs["out"] = (
            self.value_before.copy()
            if t0 < self.start_time - self.EPS
            else self.value_after.copy()
        )

    def output_update(self, t: float, dt: float) -> None:
        """Write value_before or value_after to the output port based on t.

        Args:
            t: Current simulation time in seconds.
            dt: Current time step in seconds.
        """
        self.outputs["out"] = (
            self.value_before.copy()
            if t < self.start_time - self.EPS
            else self.value_after.copy()
        )

