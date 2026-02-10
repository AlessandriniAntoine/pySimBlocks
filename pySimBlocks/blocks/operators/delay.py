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
from numpy.typing import ArrayLike

from pySimBlocks.core.block import Block


class Delay(Block):
    """
    N-step discrete delay block.

    Summary:
        Outputs a delayed version of the input signal by a fixed number of
        discrete time steps.

    Parameters (overview):
        num_delays : int
            Number of discrete delays N (N >= 1).
        initial_output : scalar or array-like, optional
            Initial value used to fill the delay buffer.
            Accepted: scalar -> (1,1), 1D -> (k,1), 2D -> (m,n).
            Scalar (1,1) can be broadcast to match the input shape when the
            first input becomes available.
        sample_time : float, optional
            Block execution period.

    I/O:
        Inputs:
            in : Input signal (must be 2D).
            reset: Optional reset signal.
        Outputs:
            out : Delayed output signal (2D).

    Notes:
        - Stateful block.
        - No direct feedthrough.
        - Output at time k is the input at time k − N.
        - Buffer shape is inferred from the first available input if not
          explicitly initialized.
        - Policy:
            + Signals are 2D arrays.
            + Buffer always exists (never None).
            + Shape is fixed either:
                * immediately if initial_output is non-scalar 2D (shape != (1,1))
                * otherwise at the first non-None input seen by the block
            + If buffer is still "unfixed" and currently scalar (1,1), it can be
              broadcast ONCE to match the first input shape.
            + After shape is fixed, any shape mismatch raises.
    """

    direct_feedthrough = False

    def __init__(
        self,
        name: str,
        num_delays: int = 1,
        initial_output: ArrayLike | None = None,
        sample_time: float | None = None,
    ):
        super().__init__(name, sample_time)

        if not isinstance(num_delays, int) or num_delays < 1:
            raise ValueError(f"[{self.name}] num_delays must be >= 1.")
        self.num_delays = num_delays

        self.inputs["in"] = None
        self.inputs["reset"] = None
        self.outputs["out"] = None

        self.state["buffer"] = None
        self.next_state["buffer"] = None

        # Shape management
        self._shape_fixed: bool = False
        self._buffer_shape: tuple[int, int] | None = None

        # Initialize buffer as (1,1) by default, but NOT fixed yet.
        self._initial_output = initial_output
        init = np.zeros((1, 1), dtype=float)

        if initial_output is not None:
            arr = self._to_2d_array("initial_output", initial_output)
            init = arr.astype(float, copy=False)

            # If user provides a non-scalar 2D initial_output, shape is fixed now.
            if not self._is_scalar_2d(init):
                self._shape_fixed = True
                self._buffer_shape = init.shape

        # Buffer always exists (never None)
        self.state["buffer"] = [init.copy() for _ in range(self.num_delays)]
        self.next_state["buffer"] = None


    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------
    def initialize(self, t0: float) -> None:
        out = self.state["buffer"][0]

        u = self.inputs["in"]
        if u is not None:
            u_arr = np.asarray(u, dtype=float)
            self._ensure_shape_and_buffer(u_arr)

            if self._is_scalar_2d(out) and self._buffer_shape != (1, 1):
                out = np.full(self._buffer_shape, float(out[0, 0]), dtype=float)
            else:
                if out.shape != self._buffer_shape:
                    raise ValueError(
                        f"[{self.name}] Initial output shape mismatch: expected {self._buffer_shape}, got {out.shape}."
                    )

        self.outputs["out"] = out

    # ------------------------------------------------------------------
    def output_update(self, t: float, dt: float) -> None:
        if not self._shape_fixed:
            u = self.inputs["in"]
            if u is not None:
                u_arr = np.asarray(u, dtype=float)
                self._ensure_shape_and_buffer(u_arr)

        self.outputs["out"] = self.state["buffer"][0].copy()

    # ------------------------------------------------------------------
    def state_update(self, t: float, dt: float) -> None:
        if self._is_reset_active():
            self._apply_reset()
            return

        u = self.inputs["in"]
        if u is None:
            raise RuntimeError(f"[{self.name}] Input 'in' is not connected or not set.")

        u_arr = np.asarray(u, dtype=float)

        self._ensure_shape_and_buffer(u_arr)

        buffer = self.state["buffer"]

        # Shift left and append u
        new_buffer = []
        for i in range(self.num_delays - 1):
            new_buffer.append(buffer[i + 1].copy())
        new_buffer.append(u_arr.copy())

        self.next_state["buffer"] = new_buffer

    # --------------------------------------------------------------------------
    # Private methods
    # --------------------------------------------------------------------------
    def _ensure_shape_and_buffer(self, u: np.ndarray) -> None:
        """
        Ensure:
            - u is 2D
            - buffer exists
            - shape is fixed at the right time
            - after shape is fixed, input must match buffer shape
        """
        if u.ndim != 2:
            raise ValueError(
                f"[{self.name}] Input 'in' must be a 2D array. Got ndim={u.ndim} with shape {u.shape}."
            )

        buf0 = self.state["buffer"][0]
        assert buf0 is not None

        # If already fixed, enforce strict match
        if self._shape_fixed:
            expected = buf0.shape
            if u.shape != expected:
                raise ValueError(
                    f"[{self.name}] Input 'in' shape mismatch: expected {expected}, got {u.shape}."
                )
            return

        # Not fixed yet: decide whether we can/should fix now
        # We fix the shape the first time we see a non-None input (whatever its shape is).
        target_shape = u.shape

        # If buffer is scalar placeholder, broadcast it to target shape (one-time)
        if self._is_scalar_2d(buf0) and target_shape != (1, 1):
            scalar = float(buf0[0, 0])
            self.state["buffer"] = [
                np.full(target_shape, scalar, dtype=float) for _ in range(self.num_delays)
            ]
            buf0 = self.state["buffer"][0]

        # If buffer is not scalar but we are not fixed yet, it must already match target shape
        # (This can happen if you later decide to relax some init logic; keep strict.)
        if buf0.shape != target_shape:
            raise ValueError(
                f"[{self.name}] Cannot infer a consistent delay shape: "
                f"buffer currently {buf0.shape} but first input is {target_shape}."
            )

        # Now we can fix shape (including (1,1))
        self._shape_fixed = True
        self._buffer_shape = target_shape

    # ------------------------------------------------------------------
    def _is_reset_active(self) -> bool:
        reset_signal = self.inputs.get("reset", None)
        if reset_signal is None:
            return False
        reset_arr = np.asarray(reset_signal)
        if reset_arr.ndim == 0:
            return bool(reset_arr)
        elif reset_arr.ndim == 1 and reset_arr.size == 1:
            return bool(reset_arr[0])
        elif reset_arr.ndim == 2 and reset_arr.shape == (1, 1):
            return bool(reset_arr[0, 0])
        else:
            raise ValueError(
                f"[{self.name}] Reset signal must be a scalar or single-element array. Got shape {reset_arr.shape}."
            )

    def _apply_reset(self) -> None:
        if self._initial_output is not None:
            arr = self._to_2d_array("initial_output", self._initial_output)
            init = arr.astype(float, copy=False)
            if self._shape_fixed and self._buffer_shape is not None:
                if self._is_scalar_2d(init) and self._buffer_shape != (1, 1):
                    scalar = float(init[0, 0])
                    init = np.full(self._buffer_shape, scalar, dtype=float)

        elif self._shape_fixed and self._buffer_shape is not None:
            init = np.zeros(self._buffer_shape, dtype=float)

        else:
            init = np.zeros((1, 1), dtype=float)

        self.state["buffer"] = [init.copy() for _ in range(self.num_delays)]
        self.next_state["buffer"] = [init.copy() for _ in range(self.num_delays)]
