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


class ZeroOrderHold(Block):
    """
    Zero-Order Hold (ZOH) block.

    Summary:
        Samples the input signal at discrete instants and holds the sampled
        value constant between sampling instants.

    Parameters:
        sample_time : float
            Sampling period Ts (> 0).

    Inputs:
        in : array (m,n)
            Input signal (must be 2D).

    Outputs:
        out : array (m,n)
            Held output signal.

    Notes:
        - Stateful block.
        - Direct feedthrough (output depends on current u only at sampling instants).
        - Shape is frozen after first resolution.
    """

    direct_feedthrough = True

    def __init__(self, name: str, sample_time: float):
        super().__init__(name, sample_time)

        if not isinstance(sample_time, (float, int)) or float(sample_time) <= 0.0:
            raise ValueError(f"[{self.name}] sample_time must be > 0.")

        self.sample_time = float(sample_time)
        self.EPS = 1e-12

        self.inputs["in"] = None
        self.outputs["out"] = None

        self.state["y"] = None
        self.next_state["y"] = None
        self.state["t_last"] = None
        self.next_state["t_last"] = None

        self._resolved_shape: tuple[int, int] | None = None


    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------
    def initialize(self, t0: float):
        u = self.inputs["in"]
        if u is None:
            raise RuntimeError(f"[{self.name}] Input 'in' is None at initialization.")

        u = self._to_2d_array("input", u)
        self._ensure_shape(u)

        y0 = u.copy()
        self.state["y"] = y0
        self.state["t_last"] = float(t0)

        self.next_state["y"] = y0.copy()
        self.next_state["t_last"] = float(t0)

        self.outputs["out"] = y0.copy()

    # ------------------------------------------------------------------
    def output_update(self, t: float, dt: float):
        u = self.inputs["in"]
        if u is None:
            raise RuntimeError(f"[{self.name}] Input 'in' is None.")

        u = self._to_2d_array("input", u)
        self._ensure_shape(u)

        t_last = self.state["t_last"]
        if t_last is None:
            raise RuntimeError(f"[{self.name}] ZOH not initialized (t_last is None).")

        # Sample if enough time elapsed
        if (t - t_last) >= self.sample_time - self.EPS:
            self.outputs["out"] = u.copy()
        else:
            self.outputs["out"] = self.state["y"].copy()

    # ------------------------------------------------------------------
    def state_update(self, t: float, dt: float):
        t_last = self.state["t_last"]
        if t_last is None:
            raise RuntimeError(f"[{self.name}] ZOH not initialized (t_last is None).")

        if (t - t_last) >= self.sample_time - self.EPS:
            self.next_state["y"] = self.outputs["out"].copy()
            self.next_state["t_last"] = float(t)
        else:
            self.next_state["y"] = self.state["y"].copy()
            self.next_state["t_last"] = float(t_last)


    # --------------------------------------------------------------------------
    # Private methods
    # --------------------------------------------------------------------------
    def _ensure_shape(self, u: np.ndarray) -> None:
        if u.ndim != 2:
            raise ValueError(
                f"[{self.name}] Input 'in' must be a 2D array. Got ndim={u.ndim} with shape {u.shape}."
            )
        if self._resolved_shape is None:
            self._resolved_shape = u.shape
            return
        if u.shape != self._resolved_shape:
            raise ValueError(
                f"[{self.name}] Input 'in' shape changed: expected {self._resolved_shape}, got {u.shape}."
            )
