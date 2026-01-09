import numpy as np
from pySimBlocks.core.block import Block


class Product(Block):
    """
    Multi-input product block.

    Summary:
        Computes a product/division of multiple input signals.

    Parameters (overview):
        operations : str of signs */
            operation bitween each input.
        multiplication : str
            Type of multiplication: Element-wise (*) or Matrix (@).
        sample_time : float, optional
            Block execution period.

    I/O:
        Inputs:
            in1, in2, ..., inN : input signals
        Output:
            out : product output signal

    Notes:
        - All inputs must have the same dimension.
        - No internal state.
    """

    def __init__(self,
        name: str,
        operations: str | None = None,
        multiplication: str = "Element-wise (*)",
        sample_time: float | None = None
    ):
        super().__init__(name, sample_time)

        # --- Validate num_inputs / signs -------------------------------------
        if operations is None:
            operations = "*"

        if not isinstance(operations, str):
            raise TypeError(f"[{self.name}] 'operations' must be a str.")

        if not isinstance(multiplication, str):
            raise TypeError(f"[{self.name}] 'multiplication' must be a str.")

        if any(s not in ("*", "/") for s in operations):
            raise ValueError(f"[{self.name}] 'operations' must contain only * or /.")

        if multiplication not in ("Element-wise (*)", "Matrix (@)"):
            raise ValueError(f"[{self.name}] 'multiplication' must be 'Element-wise (*)' or 'Matrix (@)'.")

        if multiplication == "Matrix (@)":
            raise NotImplementedError(f"[{self.name}] 'Matrix (@)' multiplication is not yet implemented.")

        self.operations = operations
        self.multiplication = multiplication
        self.num_inputs = len(self.operations) + 1

        # Create ports
        for i in range(self.num_inputs):
            self.inputs[f"in{i+1}"] = None

        self.outputs["out"] = None

    # ----------------------------------------------------------------------
    def initialize(self, t0: float):
        """If inputs are already known at initialization, compute output."""
        for i in range(self.num_inputs):
            if self.inputs[f"in{i+1}"] is None:
                self.inputs[f"in{i+1}"] = np.ones((1,1))  # dimension fallback
        self.outputs["out"] = self._compute_output()

    # ----------------------------------------------------------------------
    def output_update(self, t: float, dt: float):
        # Check all inputs & check dimension consistency
        shapes = set()
        for i in range(self.num_inputs):
            u = self.inputs[f"in{i+1}"]
            if u is None:
                raise RuntimeError(f"[{self.name}] Input 'in{i+1}' is not connected or not set.")

            u = np.asarray(u)
            if u.ndim != 2 or u.shape[1] != 1:
                raise ValueError(
                    f"[{self.name}] Input 'in{i+1}' must be a column vector (n,1). Got {u.shape}."
                )

            shapes.add(u.shape[0])

        # authorize broadcasting of scalars only
        if len(shapes) > 1:
            if shapes != {1, max(shapes)}:
                raise ValueError(f"[{self.name}] All inputs must have same dimension. Got sizes {shapes}.")

        self.outputs["out"] = self._compute_output()

    # ----------------------------------------------------------------------
    def state_update(self, t: float, dt: float):
        pass

    # ----------------------------------------------------------------------
    def _compute_output(self):
        arrays = []

        # Collect inputs
        for i in range(self.num_inputs):
            u = np.asarray(self.inputs[f"in{i+1}"], dtype=float)
            u = u.reshape(-1, 1)
            arrays.append(u)

        # Dimension handling (element-wise)
        sizes = {a.shape[0] for a in arrays}
        max_dim = max(sizes)

        if len(sizes) > 1:
            if sizes == {1, max_dim}:
                arrays = [
                    np.full((max_dim, 1), a.item()) if a.shape[0] == 1 else a
                    for a in arrays
                ]
            else:
                raise ValueError(
                    f"[{self.name}] Incompatible input dimensions for element-wise product: {sizes}"
                )

        # Compute product/division
        result = arrays[0].copy()

        for op, a in zip(self.operations, arrays[1:]):
            if op == "*":
                result *= a
            elif op == "/":
                result /= a

        return result
