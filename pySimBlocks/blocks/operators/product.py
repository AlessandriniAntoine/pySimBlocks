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


class Product(Block):
    """
    Multi-input product block.

    Summary:
        Computes a product/division of multiple input signals.

    Parameters:
        operations : str
            String of operators between inputs, using '*' and '/'.
            If length is L, number of inputs is L+1.
        multiplication : str
            "Element-wise (*)" or "Matrix (@)".
        sample_time : float, optional
            Block execution period.

    Inputs:
        in1, in2, ..., inN : array (m,n)
            Input signals (must be 2D arrays).

    Outputs:
        out : array (p,q)
            Product output.

    Notes:
        - Stateless block.
        - Direct feedthrough.
        - Shapes are frozen per input port on first use.
        - Element-wise mode supports scalar (1,1) broadcasting only.
        - Matrix mode supports '*' only; '/' is rejected.
    """

    direct_feedthrough = True

    def __init__(
        self,
        name: str,
        operations: str | None = None,
        multiplication: str = "Element-wise (*)",
        sample_time: float | None = None,
    ):
        super().__init__(name, sample_time)

        if operations is None:
            operations = "*"

        if not isinstance(operations, str):
            raise TypeError(f"[{self.name}] 'operations' must be a str.")
        if any(op not in ("*", "/") for op in operations):
            raise ValueError(f"[{self.name}] 'operations' must contain only '*' or '/'.")

        if not isinstance(multiplication, str):
            raise TypeError(f"[{self.name}] 'multiplication' must be a str.")
        if multiplication not in ("Element-wise (*)", "Matrix (@)"):
            raise ValueError(
                f"[{self.name}] 'multiplication' must be 'Element-wise (*)' or 'Matrix (@)'."
            )

        if multiplication == "Matrix (@)" and "/" in operations:
            raise ValueError(f"[{self.name}] Division '/' is not supported in 'Matrix (@)' mode.")

        self.operations = operations
        self.multiplication = multiplication
        self.num_inputs = len(self.operations) + 1

        for i in range(self.num_inputs):
            self.inputs[f"in{i+1}"] = None

        self.outputs["out"] = None

        # Shape freezing per input port
        self._input_shapes: dict[str, tuple[int, int]] = {}


    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------
    def initialize(self, t0: float):
        # No "fallback" values: missing inputs should be detected normally
        # but for init, if any input missing, output stays None
        for i in range(self.num_inputs):
            if self.inputs[f"in{i+1}"] is None:
                self.outputs["out"] = None
                return
        self.outputs["out"] = self._compute_output()

    # ------------------------------------------------------------------
    def output_update(self, t: float, dt: float):
        self.outputs["out"] = self._compute_output()

    # ------------------------------------------------------------------
    def state_update(self, t: float, dt: float):
        pass


    # --------------------------------------------------------------------------
    # Private methods
    # --------------------------------------------------------------------------
    def _get_input_2d(self, port: str) -> np.ndarray:
        u = self.inputs[port]
        if u is None:
            raise RuntimeError(f"[{self.name}] Input '{port}' is not connected or not set.")
        u_arr = self._to_2d_array(port, u)  # uses Block helper
        # freeze shape per port
        if port not in self._input_shapes:
            self._input_shapes[port] = u_arr.shape
        elif u_arr.shape != self._input_shapes[port]:
            raise ValueError(
                f"[{self.name}] Input '{port}' shape changed: expected {self._input_shapes[port]}, got {u_arr.shape}."
            )
        return u_arr

    # ------------------------------------------------------------------
    def _compute_output(self) -> np.ndarray:
        arrays = [self._get_input_2d(f"in{i+1}") for i in range(self.num_inputs)]

        if self.multiplication == "Element-wise (*)":
            # Only scalar (1,1) broadcasting allowed
            non_scalar_shapes = {a.shape for a in arrays if not self._is_scalar_2d(a)}
            if len(non_scalar_shapes) > 1:
                raise ValueError(
                    f"[{self.name}] Incompatible input shapes for element-wise product: {sorted(non_scalar_shapes)}."
                )

            # target shape = the unique non-scalar shape if any, else (1,1)
            target_shape = (1, 1) if len(non_scalar_shapes) == 0 else next(iter(non_scalar_shapes))

            def expand(a: np.ndarray) -> np.ndarray:
                if self._is_scalar_2d(a) and target_shape != (1, 1):
                    return np.full(target_shape, float(a[0, 0]), dtype=float)
                return a.astype(float)

            arrays = [expand(a) for a in arrays]

            result = arrays[0].copy()
            for op, a in zip(self.operations, arrays[1:]):
                if op == "*":
                    result = result * a
                else:  # "/"
                    result = result / a
            return result

        # -------------------- Matrix (@) mode
        # Only '*' allowed by __init__ guard
        result = arrays[0].astype(float)

        for a in arrays[1:]:
            a = a.astype(float)

            # scalar scaling cases
            if self._is_scalar_2d(result) and not self._is_scalar_2d(a):
                result = float(result[0, 0]) * a
                continue
            if not self._is_scalar_2d(result) and self._is_scalar_2d(a):
                result = result * float(a[0, 0])
                continue
            if self._is_scalar_2d(result) and self._is_scalar_2d(a):
                result = np.array([[float(result[0, 0]) * float(a[0, 0])]], dtype=float)
                continue

            # true matrix multiplication
            if result.shape[1] != a.shape[0]:
                raise ValueError(
                    f"[{self.name}] Incompatible dimensions for matrix product: "
                    f"{result.shape} @ {a.shape}."
                )
            result = result @ a

        return result
