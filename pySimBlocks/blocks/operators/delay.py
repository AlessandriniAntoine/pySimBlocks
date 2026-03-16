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

from pySimBlocks.core.block import Block


class Delay(Block):
    """N-step discrete delay block.

    Outputs a delayed version of the input signal by a fixed number of discrete
    time steps. The output at time k is the input at time k − N:

        y[k] = u[k - N]

    The buffer shape is inferred from the first non-None input unless an
    explicit ``initial_output`` of non-scalar shape is provided. A scalar (1,1)
    initial value is broadcast to match the first input. Once the shape is
    fixed, any mismatch raises an error.

    Attributes:
        num_delays: Number of discrete steps N (>= 1).
    """

    direct_feedthrough = False

    def __init__(
        self,
        name: str,
        num_delays: int = 1,
        initial_output: ArrayLike | None = None,
        sample_time: float | None = None,
    ):
        """Initialize a Delay block.

        Args:
            name: Unique identifier for this block instance.
            num_delays: Number of discrete steps to delay the input. Must be
                >= 1.
            initial_output: Initial value used to fill the delay buffer.
                Accepted shapes: scalar, 1D, or 2D. A non-scalar 2D value
                fixes the buffer shape immediately.
            sample_time: Sampling period in seconds, or None to use the global
                simulation dt.

        Raises:
            ValueError: If ``num_delays`` is not a positive integer.
        """
        super().__init__(name, sample_time)

        if not isinstance(num_delays, int) or num_delays < 1:
            raise ValueError(f"[{self.name}] num_delays must be >= 1.")
        self.num_delays = num_delays

        self.inputs["in"] = None
        self.inputs["reset"] = None
        self.outputs["out"] = None

        self.state["buffer"] = None
        self.next_state["buffer"] = None

        self._shape_fixed: bool = False
        self._buffer_shape: tuple[int, int] | None = None

        self._initial_output = initial_output
        init = np.zeros((1, 1), dtype=float)

        if initial_output is not None:
            arr = self._to_2d_array("initial_output", initial_output)
            init = arr.astype(float, copy=False)

            if not self._is_scalar_2d(init):
                self._shape_fixed = True
                self._buffer_shape = init.shape

        self.state["buffer"] = [init.copy() for _ in range(self.num_delays)]
        self.next_state["buffer"] = None


    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------

    def initialize(self, t0: float) -> None:
        """Set the initial output from the buffer, resolving shape if input is available.

        Args:
            t0: Initial simulation time in seconds.

        Raises:
            ValueError: If the initial output shape is inconsistent with the
                resolved buffer shape.
        """
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

    def output_update(self, t: float, dt: float) -> None:
        """Output the oldest buffer entry.

        Args:
            t: Current simulation time in seconds.
            dt: Current time step in seconds.
        """
        if not self._shape_fixed:
            u = self.inputs["in"]
            if u is not None:
                u_arr = np.asarray(u, dtype=float)
                self._ensure_shape_and_buffer(u_arr)

        self.outputs["out"] = self.state["buffer"][0].copy()

    def state_update(self, t: float, dt: float) -> None:
        """Shift the buffer left and append the current input.

        Args:
            t: Current simulation time in seconds.
            dt: Current time step in seconds.

        Raises:
            RuntimeError: If input ``'in'`` is not connected.
            ValueError: If the input is not 2D or its shape is inconsistent
                with the buffer.
        """
        if self._is_reset_active():
            self._apply_reset()
            return

        u = self.inputs["in"]
        if u is None:
            raise RuntimeError(f"[{self.name}] Input 'in' is not connected or not set.")

        u_arr = np.asarray(u, dtype=float)

        self._ensure_shape_and_buffer(u_arr)

        buffer = self.state["buffer"]

        new_buffer = []
        for i in range(self.num_delays - 1):
            new_buffer.append(buffer[i + 1].copy())
        new_buffer.append(u_arr.copy())

        self.next_state["buffer"] = new_buffer


    # --------------------------------------------------------------------------
    # Private methods
    # --------------------------------------------------------------------------

    def _ensure_shape_and_buffer(self, u: np.ndarray) -> None:
        """Validate input shape and fix the buffer shape on the first non-None input."""
        if u.ndim != 2:
            raise ValueError(
                f"[{self.name}] Input 'in' must be a 2D array. Got ndim={u.ndim} with shape {u.shape}."
            )

        buf0 = self.state["buffer"][0]
        assert buf0 is not None

        if self._shape_fixed:
            expected = buf0.shape
            if u.shape != expected:
                raise ValueError(
                    f"[{self.name}] Input 'in' shape mismatch: expected {expected}, got {u.shape}."
                )
            return

        target_shape = u.shape

        if self._is_scalar_2d(buf0) and target_shape != (1, 1):
            scalar = float(buf0[0, 0])
            self.state["buffer"] = [
                np.full(target_shape, scalar, dtype=float) for _ in range(self.num_delays)
            ]
            buf0 = self.state["buffer"][0]

        if buf0.shape != target_shape:
            raise ValueError(
                f"[{self.name}] Cannot infer a consistent delay shape: "
                f"buffer currently {buf0.shape} but first input is {target_shape}."
            )

        self._shape_fixed = True
        self._buffer_shape = target_shape

    def _is_reset_active(self) -> bool:
        """Return True if the reset signal is active (truthy scalar)."""
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
        """Reset the buffer to the initial output or zeros."""
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
