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


class Product(Block):
    """Multi-input product block.

    Computes a product or division of multiple 2D input signals. The number of
    inputs is ``len(operations) + 1``. Two multiplication modes are supported:

    - **Element-wise**: applies ``*`` and ``/`` component-wise with scalar
      (1,1) broadcasting only.
    - **Matrix**: applies ``@`` sequentially; division is not supported.

    Input shapes are frozen per port after their first use.

    Attributes:
        operations: String of ``'*'`` and ``'/'`` operators, one per adjacent
            pair of inputs.
        multiplication: Active multiplication mode string.
        num_inputs: Total number of input ports.
    """

    direct_feedthrough = True

    def __init__(
        self,
        name: str,
        operations: str | None = None,
        multiplication: str = "Element-wise (*)",
        sample_time: float | None = None,
    ):
        """Initialize a Product block.

        Args:
            name: Unique identifier for this block instance.
            operations: String of ``'*'`` and ``'/'`` operators between inputs.
                Defaults to ``'*'`` (two inputs, one multiplication).
            multiplication: Multiplication mode. Must be ``'Element-wise (*)'``
                or ``'Matrix (@)'``.
            sample_time: Sampling period in seconds, or None to use the global
                simulation dt.

        Raises:
            TypeError: If ``operations`` or ``multiplication`` are not strings.
            ValueError: If ``operations`` contains unsupported characters, if
                ``multiplication`` is not a valid mode, or if ``'/'`` is used
                in matrix mode.
        """
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

        self._input_shapes: dict[str, tuple[int, int]] = {}


    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------

    def initialize(self, t0: float) -> None:
        """Compute the initial output if all inputs are available.

        Args:
            t0: Initial simulation time in seconds.
        """
        for i in range(self.num_inputs):
            if self.inputs[f"in{i+1}"] is None:
                self.outputs["out"] = None
                return
        self.outputs["out"] = self._compute_output()

    def output_update(self, t: float, dt: float) -> None:
        """Compute the product and write the result to the output port.

        Args:
            t: Current simulation time in seconds.
            dt: Current time step in seconds.

        Raises:
            RuntimeError: If any input port is not connected.
            ValueError: If input shapes are inconsistent or incompatible with
                the multiplication mode.
        """
        self.outputs["out"] = self._compute_output()

    def state_update(self, t: float, dt: float) -> None:
        """No-op: Product is a stateless block.

        Args:
            t: Current simulation time in seconds.
            dt: Current time step in seconds.
        """
        pass


    # --------------------------------------------------------------------------
    # Private methods
    # --------------------------------------------------------------------------

    def _get_input_2d(self, port: str) -> np.ndarray:
        """Retrieve, validate, and shape-freeze a single input port."""
        u = self.inputs[port]
        if u is None:
            raise RuntimeError(f"[{self.name}] Input '{port}' is not connected or not set.")
        u_arr = self._to_2d_array(port, u)
        if port not in self._input_shapes:
            self._input_shapes[port] = u_arr.shape
        elif u_arr.shape != self._input_shapes[port]:
            raise ValueError(
                f"[{self.name}] Input '{port}' shape changed: expected {self._input_shapes[port]}, got {u_arr.shape}."
            )
        return u_arr

    def _compute_output(self) -> np.ndarray:
        """Compute the product of all inputs according to the multiplication mode."""
        arrays = [self._get_input_2d(f"in{i+1}") for i in range(self.num_inputs)]

        if self.multiplication == "Element-wise (*)":
            non_scalar_shapes = {a.shape for a in arrays if not self._is_scalar_2d(a)}
            if len(non_scalar_shapes) > 1:
                raise ValueError(
                    f"[{self.name}] Incompatible input shapes for element-wise product: {sorted(non_scalar_shapes)}."
                )

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
                else:
                    result = result / a
            return result

        result = arrays[0].astype(float)

        for a in arrays[1:]:
            a = a.astype(float)

            if self._is_scalar_2d(result) and not self._is_scalar_2d(a):
                result = float(result[0, 0]) * a
                continue
            if not self._is_scalar_2d(result) and self._is_scalar_2d(a):
                result = result * float(a[0, 0])
                continue
            if self._is_scalar_2d(result) and self._is_scalar_2d(a):
                result = np.array([[float(result[0, 0]) * float(a[0, 0])]], dtype=float)
                continue

            if result.shape[1] != a.shape[0]:
                raise ValueError(
                    f"[{self.name}] Incompatible dimensions for matrix product: "
                    f"{result.shape} @ {a.shape}."
                )
            result = result @ a

        return result
