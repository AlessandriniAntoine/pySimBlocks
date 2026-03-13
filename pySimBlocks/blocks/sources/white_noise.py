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


class WhiteNoise(BlockSource):
    """Multi-dimensional Gaussian white noise source block.

    Generates independent Gaussian noise samples at each simulation step,
    element-wise on a 2D output array: 

        y = mean + std * N(0,1).

    Parameters may be scalars, vectors, or matrices. Only scalar-to-shape
    broadcasting is allowed; all non-scalar parameters must share the same
    shape.

    Attributes:
        mean: Mean value of the noise, as a 2D array.
        std: Standard deviation of the noise, as a 2D array.
        rng: NumPy random generator instance used to draw samples.
    """

    def __init__(
        self,
        name: str,
        mean: ArrayLike = 0.0,
        std: ArrayLike = 1.0,
        seed: int | None = None,
        sample_time: float | None = None,
    ):
        """Initialize a WhiteNoise block.

        Args:
            name: Unique identifier for this block instance.
            mean: Mean value of the noise. Can be scalar, vector, or matrix.
            std: Standard deviation of the noise. Can be scalar, vector,
                or matrix. Must be >= 0 element-wise.
            seed: Random seed for reproducibility. None for a random seed.
            sample_time: Sampling period in seconds, or None to use the
                global simulation dt.

        Raises:
            ValueError: If std is negative for any element, or if non-scalar
                parameters have incompatible shapes.
        """
        super().__init__(name, sample_time)

        M = self._to_2d_array("mean", mean, dtype=float)
        S = self._to_2d_array("std", std, dtype=float)

        target_shape = self._resolve_common_shape({
            "mean": M,
            "std": S,
        })

        self.mean = self._broadcast_scalar_only("mean", M, target_shape)
        self.std = self._broadcast_scalar_only("std", S, target_shape)

        if np.any(self.std < 0.0):
            raise ValueError(f"[{self.name}] std must be >= 0 (element-wise).")

        self.rng = np.random.default_rng(seed)

        self.outputs["out"] = np.zeros(target_shape, dtype=float)


    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------

    def initialize(self, t0: float) -> None:
        """Draw an initial noise sample and set the output.

        Args:
            t0: Initial simulation time in seconds.
        """
        self.outputs["out"] = self._draw()

    def output_update(self, t: float, dt: float) -> None:
        """Draw a new noise sample and write it to the output port.

        Args:
            t: Current simulation time in seconds.
            dt: Current time step in seconds.
        """
        self.outputs["out"] = self._draw()


    # --------------------------------------------------------------------------
    # Private methods
    # --------------------------------------------------------------------------

    def _draw(self) -> np.ndarray:
        """Sample a Gaussian noise array with the configured mean and std."""
        return self.mean + self.std * self.rng.standard_normal(self.mean.shape)
