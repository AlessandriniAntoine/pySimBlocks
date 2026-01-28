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


class Sum(Block):
    """
    Multi-input summation block.

    Summary:
        Computes an element-wise sum/subtraction of multiple input signals.

    Parameters:
        signs : str
            Sequence of '+' and '-' defining the sign of each input (e.g. '++-', '+-').
            If None, defaults to '++' (two inputs).
        sample_time : float, optional
            Block execution period.

    Inputs:
        in1, in2, ..., inN : array (m,n)
            Input signals (must be 2D).
            Scalar (1,1) inputs can be broadcast to the common target shape.

    Outputs:
        out : array (m,n)
            Element-wise signed sum.

    Notes:
        - Direct feedthrough.
        - Stateless.
        - Shape policy:
            * all inputs must be 2D
            * all non-scalar inputs must share exactly the same shape
            * scalar (1,1) inputs can be broadcast to that shape
            * no other broadcasting is allowed
    """

    direct_feedthrough = True

    def __init__(
        self,
        name: str,
        signs: str | None = None,
        sample_time: float | None = None,
    ):
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
        """
        If all inputs are already available, compute output.
        Otherwise output stays None until first output_update().
        """
        if any(self.inputs[f"in{i+1}"] is None for i in range(self.num_inputs)):
            self.outputs["out"] = None
            return

        self.outputs["out"] = self._compute_output()

    # ------------------------------------------------------------------
    def output_update(self, t: float, dt: float) -> None:
        # Validate presence + 2D constraint
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

    # ------------------------------------------------------------------
    def state_update(self, t: float, dt: float) -> None:
        return  # stateless


    # --------------------------------------------------------------------------
    # Private methods
    # --------------------------------------------------------------------------
    def _resolve_common_shape(self, arrays: list[np.ndarray]) -> tuple[int, int]:
        """
        Determine target shape among inputs.

        - Scalars (1,1) are broadcastable
        - Any non-scalar fixes the target shape
        - If multiple non-scalars exist, they must all match exactly
        - If all scalars => target is (1,1)
        """
        non_scalar_shapes = {a.shape for a in arrays if not self._is_scalar_2d(a)}

        if len(non_scalar_shapes) == 0:
            return (1, 1)

        if len(non_scalar_shapes) == 1:
            return next(iter(non_scalar_shapes))

        raise ValueError(
            f"[{self.name}] Inconsistent input shapes for Sum: "
            f"{[a.shape for a in arrays]}. All non-scalar inputs must have the same shape."
        )

    # ------------------------------------------------------------------
    def _broadcast_scalar_only(self, arr: np.ndarray, target_shape: tuple[int, int], input_name: str) -> np.ndarray:
        """
        Broadcast only scalar (1,1) to target_shape.
        Non-scalar must match target_shape exactly.
        """
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

    # ------------------------------------------------------------------
    def _compute_output(self, prevalidated_arrays: list[np.ndarray] | None = None) -> np.ndarray:
        """
        Compute signed element-wise sum with strict scalar-only broadcast.
        """
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
