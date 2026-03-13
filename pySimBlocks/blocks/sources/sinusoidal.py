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


class Sinusoidal(BlockSource):
    """Multi-dimensional sinusoidal signal source block.

    Generates sinusoidal signals element-wise on a 2D output array:
        y(t) = amplitude * sin(2*pi*frequency*t + phase) + offset

    Parameters may be scalars, vectors, or matrices. Only scalar-to-shape
    broadcasting is allowed; all non-scalar parameters must share the same
    shape.

    Attributes:
        amplitude: Sinusoidal amplitude, as a 2D array.
        frequency: Frequency in Hz, as a 2D array.
        offset: DC offset added to the signal, as a 2D array.
        phase: Phase shift in radians, as a 2D array.
    """

    def __init__(
        self,
        name: str,
        amplitude: ArrayLike,
        frequency: ArrayLike,
        offset: ArrayLike = 0.0,
        phase: ArrayLike = 0.0,
        sample_time: float | None = None,
    ):
        """Initialize a Sinusoidal block.

        Args:
            name: Unique identifier for this block instance.
            amplitude: Sinusoidal amplitude. Can be scalar, vector, or matrix.
            frequency: Frequency in Hz. Can be scalar, vector, or matrix.
            offset: DC offset added to the signal. Can be scalar, vector,
                or matrix.
            phase: Phase shift in radians. Can be scalar, vector, or matrix.
            sample_time: Sampling period in seconds, or None to use the
                global simulation dt.

        Raises:
            ValueError: If non-scalar parameters have incompatible shapes.
        """
        super().__init__(name, sample_time)

        A = self._to_2d_array("amplitude", amplitude, dtype=float)
        F = self._to_2d_array("frequency", frequency, dtype=float)
        O = self._to_2d_array("offset", offset, dtype=float)
        P = self._to_2d_array("phase", phase, dtype=float)

        target_shape = self._resolve_common_shape({
            "amplitude": A,
            "frequency": F,
            "offset": O,
            "phase": P,
        })

        self.amplitude = self._broadcast_scalar_only("amplitude", A, target_shape)
        self.frequency = self._broadcast_scalar_only("frequency", F, target_shape)
        self.offset = self._broadcast_scalar_only("offset", O, target_shape)
        self.phase = self._broadcast_scalar_only("phase", P, target_shape)

        self.outputs["out"] = np.zeros(target_shape, dtype=float)


    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------

    def initialize(self, t0: float) -> None:
        """Compute and set the output at the initial time t0.

        Args:
            t0: Initial simulation time in seconds.
        """
        self._compute_output(t0)

    def output_update(self, t: float, dt: float) -> None:
        """Compute and write the sinusoidal value to the output port.

        Args:
            t: Current simulation time in seconds.
            dt: Current time step in seconds.
        """
        self._compute_output(t)


    # --------------------------------------------------------------------------
    # Private methods
    # --------------------------------------------------------------------------

    def _compute_output(self, t: float) -> None:
        """Evaluate the sinusoidal formula at time t and write to outputs."""
        self.outputs["out"] = (
            self.amplitude
            * np.sin(2.0 * np.pi * self.frequency * t + self.phase)
            + self.offset
        )
