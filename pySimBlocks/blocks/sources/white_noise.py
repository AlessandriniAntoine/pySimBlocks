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


class WhiteNoise(BlockSource):
    """
    Multi-dimensional Gaussian white noise source block (Option B).

    Summary:
        Generates independent Gaussian noise samples at each simulation step,
        element-wise on a 2D output array:
            y = mean + std * N(0,1)

        Parameters may be scalars, vectors, or matrices. Only scalar-to-shape
        broadcasting is allowed; all non-scalar parameters must share the same
        shape.

    Parameters (overview):
        mean : float or array-like, optional
            Mean value of the noise.
        std : float or array-like, optional
            Standard deviation of the noise (must be >= 0 element-wise).
        seed : int, optional
            Random seed for reproducibility.
        sample_time : float, optional
            Block execution period.

    Outputs:
        out : noise output signal (2D ndarray)

    Notes:
        - Stateless (but uses an internal RNG).
        - Normalization:
            scalar -> (1,1), 1D -> (n,1), 2D -> (m,n)
        - Broadcasting:
            Only (1,1) scalars are broadcast to the common shape.
            No NumPy broadcasting beyond that.
        - No implicit flattening is performed.
    """

    def __init__(
        self,
        name: str,
        mean: ArrayLike = 0.0,
        std: ArrayLike = 1.0,
        seed: int | None = None,
        sample_time: float | None = None,
    ):
        super().__init__(name, sample_time)

        M = self._to_2d_array("mean", mean, dtype=float)
        S = self._to_2d_array("std", std, dtype=float)

        target_shape = self._resolve_common_shape({
            "mean": M,
            "std": S,
        })

        self.mean = self._broadcast_scalar_only("mean", M, target_shape)
        self.std = self._broadcast_scalar_only("std", S, target_shape)

        # Validate std >= 0 element-wise
        if np.any(self.std < 0.0):
            raise ValueError(f"[{self.name}] std must be >= 0 (element-wise).")

        self.rng = np.random.default_rng(seed)

        self.outputs["out"] = np.zeros(target_shape, dtype=float)


    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------
    def initialize(self, t0: float) -> None:
        self.outputs["out"] = self._draw()

    # ------------------------------------------------------------------
    def output_update(self, t: float, dt: float) -> None:
        self.outputs["out"] = self._draw()
    

    # --------------------------------------------------------------------------
    # Private methods
    # --------------------------------------------------------------------------
    def _draw(self) -> np.ndarray:
        return self.mean + self.std * self.rng.standard_normal(self.mean.shape)
