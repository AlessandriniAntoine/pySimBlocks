import numpy as np
from pySimBlocks.core.block import Block


class Sum(Block):
    """
    Multi-input summation block.

    Summary:
        Computes a sum/substraction of multiple input signals.

    Parameters (overview):
        signs : str of signs +-
            Sign associated with each input.
        sample_time : float, optional
            Block execution period.

    I/O:
        Inputs:
            in1, in2, ..., inN : input signals
        Output:
            out : summed output signal

    Notes:
        - All inputs must have the same dimension.
        - No internal state.
    """

    def __init__(self,
        name: str,
        signs: str | None = None,
        sample_time: float | None = None
    ):
        super().__init__(name, sample_time)

        # --- Validate num_inputs / signs -------------------------------------
        if signs is None:
            signs = "++"

        if not isinstance(signs, str):
            raise TypeError(f"[{self.name}] 'signs' must be a str.")

        if any(s not in ("+", "-") for s in signs):
            raise ValueError(f"[{self.name}] 'signs' must contain only + or -.")

        self.signs = [1. if s == "+" else -1. for s in signs]
        self.num_inputs = len(self.signs)

        # Create ports
        for i in range(self.num_inputs):
            self.inputs[f"in{i+1}"] = None

        self.outputs["out"] = None

    # ----------------------------------------------------------------------
    def initialize(self, t0: float):
        """If inputs are already known at initialization, compute output."""
        for i in range(self.num_inputs):
            if self.inputs[f"in{i+1}"] is None:
                self.inputs[f"in{i+1}"] = np.zeros((1,1))  # dimension fallback
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
                    f"[{self.name}] Incompatible input dimensions for element-wise sum: {sizes}"
                )

        total = None
        for s, u in zip(self.signs, arrays):
            if total is None:
                total = s * u
            else:
                total += s * u

        return total
