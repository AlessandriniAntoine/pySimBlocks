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
from pySimBlocks.core.block import Block


class ExternalOutput(Block):
    """External output interface block.

    Pass-through block for exposing model signals to the real-time external
    side. Accepts scalar, (n,) or (n,1) inputs and forwards them as a strict
    (n,1) column vector. The output shape is frozen after the first non-None
    input and cannot change during the simulation.
    """

    direct_feedthrough = True

    def __init__(self, name: str, sample_time: float | None = None):
        """Initialize an ExternalOutput block.

        Args:
            name: Unique identifier for this block instance.
            sample_time: Sampling period in seconds, or None to use the
                global simulation dt.
        """
        super().__init__(name, sample_time)
        self.inputs["in"] = None
        self.outputs["out"] = None
        self._resolved_shape: tuple[int, int] | None = None


    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------

    def initialize(self, t0: float) -> None:
        """Set the output to None if no input is available, or forward the input.

        Args:
            t0: Initial simulation time in seconds.
        """
        u = self.inputs["in"]
        if u is None:
            self.outputs["out"] = None
            return

        self.outputs["out"] = self._to_col_vec(u)

    def output_update(self, t: float, dt: float) -> None:
        """Forward the input to the output as a column vector.

        Args:
            t: Current simulation time in seconds.
            dt: Current time step in seconds.

        Raises:
            RuntimeError: If input ``in`` is not set.
            ValueError: If the input shape is incompatible or has changed.
        """
        u = self.inputs["in"]
        if u is None:
            raise RuntimeError(f"[{self.name}] Missing input 'in'.")
        self.outputs["out"] = self._to_col_vec(u)

    def state_update(self, t: float, dt: float) -> None:
        """No-op: ExternalOutput carries no internal state."""


    # --------------------------------------------------------------------------
    # Private methods
    # --------------------------------------------------------------------------

    def _to_col_vec(self, value) -> np.ndarray:
        """Normalize value to a (n,1) column vector and enforce frozen shape."""
        arr = np.asarray(value, dtype=float)

        if arr.ndim == 0:
            arr = arr.reshape(1, 1)
        elif arr.ndim == 1:
            arr = arr.reshape(-1, 1)
        elif arr.ndim == 2 and arr.shape[1] == 1:
            pass
        else:
            raise ValueError(
                f"[{self.name}] Input 'in' must be scalar, (n,), or (n,1). Got shape {arr.shape}."
            )

        if self._resolved_shape is None:
            self._resolved_shape = arr.shape
        elif arr.shape != self._resolved_shape:
            raise ValueError(
                f"[{self.name}] Input 'in' shape changed: expected {self._resolved_shape}, got {arr.shape}."
            )

        return arr
