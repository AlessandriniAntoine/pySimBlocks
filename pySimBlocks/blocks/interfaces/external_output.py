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
from pySimBlocks.core.block import Block


class ExternalOutput(Block):
    """
    External output interface block.

    Summary:
        Pass-through block for external real-time commands/values.

    Parameters:
        sample_time: float, optional
            Execution period of the block. If not specified, the simulator time
            step is used.

    I/O:
        Input:
            in: array (n,1)
                Value produced by the model. Scalar, (n,), (n,1) accepted.
        Output:
            out: array (n,1)
                Value forwarded to the external side as a column vector (n,1).

    Policy:
        - Accepts scalar, (n,), (n,1)
        - Outputs strict (n,1)
        - Once shape is known, it is frozen (cannot change)
    """
    direct_feedthrough = True

    def __init__(self, name: str, sample_time: float | None = None):
        super().__init__(name, sample_time)
        self.inputs["in"] = None
        self.outputs["out"] = None
        self._resolved_shape: tuple[int, int] | None = None


    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------
    def initialize(self, t0: float) -> None:
        u = self.inputs["in"]
        if u is None:
            self.outputs["out"] = None
            return

        self.outputs["out"] = self._to_col_vec(u)

    # ------------------------------------------------------------------
    def output_update(self, t: float, dt: float) -> None:
        u = self.inputs["in"]
        if u is None:
            raise RuntimeError(f"[{self.name}] Missing input 'in'.")
        self.outputs["out"] = self._to_col_vec(u)

    # ------------------------------------------------------------------
    def state_update(self, t: float, dt: float) -> None:
        pass


    # --------------------------------------------------------------------------
    # Private methods
    # --------------------------------------------------------------------------
    def _to_col_vec(self, value) -> np.ndarray:
        arr = np.asarray(value, dtype=float)

        # scalar
        if arr.ndim == 0:
            arr = arr.reshape(1, 1)

        # vector (n,)
        elif arr.ndim == 1:
            arr = arr.reshape(-1, 1)

        # column (n,1)
        elif arr.ndim == 2 and arr.shape[1] == 1:
            pass

        else:
            raise ValueError(
                f"[{self.name}] Input 'in' must be scalar, (n,), or (n,1). Got shape {arr.shape}."
            )

        # Freeze shape
        if self._resolved_shape is None:
            self._resolved_shape = arr.shape
        elif arr.shape != self._resolved_shape:
            raise ValueError(
                f"[{self.name}] Input 'in' shape changed: expected {self._resolved_shape}, got {arr.shape}."
            )

        return arr



