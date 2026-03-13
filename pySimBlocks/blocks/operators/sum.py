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

from pySimBlocks.core.block import Block


class Sum(Block):
    """Multi-input signed summation block.

    Computes an element-wise signed sum of multiple 2D input signals. All
    non-scalar inputs must share the same shape; scalar (1,1) inputs are
    broadcast to that shape.

    Attributes:
        signs: List of +1.0 or -1.0 coefficients, one per input port.
        num_inputs: Number of input ports.
    """

    direct_feedthrough = True

    def __init__(
        self,
        name: str,
        signs: str | None = None,
        sample_time: float | None = None,
    ):
        """Initialize a Sum block.

        Args:
            name: Unique identifier for this block instance.
            signs: Sequence of ``'+'`` and ``'-'`` defining the sign of each
                input (e.g. ``'++-'``, ``'+-'``). Defaults to ``'++'`` (two
                positive inputs).
            sample_time: Sampling period in seconds, or None to use the global
                simulation dt.

        Raises:
            TypeError: If ``signs`` is not a string.
            ValueError: If ``signs`` is empty or contains characters other than
                ``'+'`` and ``'-'``.
        """
        super().__init__(name, sample_time)

        if signs is None:
            signs = "++"

        if not isinstance(signs, str):
            raise TypeError(f"[{self.name}] 'signs' must be a str.")

        if len(signs) == 0:
            raise ValueError(f"[{self.name}] 'signs' must not be empty.")

        if any(s not in ("+", "-") for s in signs):
            raise ValueError(f"[{self.name}] 'signs' must contain only '+' or '-'.")

        self.signs = [1.0 if s == "+" else -1.0 for s in signs]
        self.num_inputs = len(self.signs)

        for i in range(self.num_inputs):
            self.inputs[f"in{i+1}"] = None

        self.outputs["out"] = None


    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------

    def initialize(self, t0: float) -> None:
        """Compute the initial output if all inputs are available.

        Args:
            t0: Initial simulation time in seconds.
        """
        if any(self.inputs[f"in{i+1}"] is None for i in range(self.num_inputs)):
            self.outputs["out"] = None
            return

        self.outputs["out"] = self._compute_output()

    def output_update(self, t: float, dt: float) -> None:
        """Compute the signed element-wise sum and write it to the output port.

        Args:
            t: Current simulation time in seconds.
            dt: Current time step in seconds.

        Raises:
            RuntimeError: If any input port is not connected.
            ValueError: If any input is not 2D or non-scalar inputs have
                inconsistent shapes.
        """
        arrays = []
        for i in range(self.num_inputs):
            key = f"in{i+1}"
            u = self.inputs[key]
            if u is None:
                raise RuntimeError(f"[{self.name}] Input '{key}' is not connected or not set.")

            a = np.asarray(u, dtype=float)
            if a.ndim != 2:
                raise ValueError(
                    f"[{self.name}] Input '{key}' must be a 2D array. Got ndim={a.ndim} with shape {a.shape}."
                )
            arrays.append(a)

        self.outputs["out"] = self._compute_output(prevalidated_arrays=arrays)

    def state_update(self, t: float, dt: float) -> None:
        """No-op: Sum is a stateless block.

        Args:
            t: Current simulation time in seconds.
            dt: Current time step in seconds.
        """
        return


    # --------------------------------------------------------------------------
    # Private methods
    # --------------------------------------------------------------------------

    def _resolve_common_shape(self, arrays: list[np.ndarray]) -> tuple[int, int]:
        """Determine the target shape from the set of input arrays."""
        non_scalar_shapes = {a.shape for a in arrays if not self._is_scalar_2d(a)}

        if len(non_scalar_shapes) == 0:
            return (1, 1)

        if len(non_scalar_shapes) == 1:
            return next(iter(non_scalar_shapes))

        raise ValueError(
            f"[{self.name}] Inconsistent input shapes for Sum: "
            f"{[a.shape for a in arrays]}. All non-scalar inputs must have the same shape."
        )

    def _broadcast_scalar_only(self, arr: np.ndarray, target_shape: tuple[int, int], input_name: str) -> np.ndarray:
        """Broadcast scalar (1,1) to target shape; reject non-scalar shape mismatches."""
        if self._is_scalar_2d(arr):
            if target_shape == (1, 1):
                return arr.astype(float, copy=False)
            return np.full(target_shape, float(arr[0, 0]), dtype=float)

        if arr.shape != target_shape:
            raise ValueError(
                f"[{self.name}] Input '{input_name}' shape {arr.shape} is incompatible with target shape {target_shape}. "
                f"Only scalar (1,1) inputs can be broadcast."
            )
        return arr.astype(float, copy=False)

    def _compute_output(self, prevalidated_arrays: list[np.ndarray] | None = None) -> np.ndarray:
        """Compute the signed element-wise sum with scalar-only broadcasting."""
        if prevalidated_arrays is None:
            arrays = [np.asarray(self.inputs[f"in{i+1}"], dtype=float) for i in range(self.num_inputs)]
        else:
            arrays = prevalidated_arrays

        target_shape = self._resolve_common_shape(arrays)

        total = np.zeros(target_shape, dtype=float)
        for i, (s, a) in enumerate(zip(self.signs, arrays), start=1):
            a2 = self._broadcast_scalar_only(a, target_shape, input_name=f"in{i}")
            total += s * a2

        return total
