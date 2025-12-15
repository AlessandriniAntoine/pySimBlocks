import numpy as np
from pySimBlocks.core.block import Block


class Sum(Block):
    """
    Multi-input summation block.

    Description:
        Computes:
            out = s1*in1 + s2*in2 + ... + sN*inN
        where each si ∈ {+1, -1}.

    Parameters:
        name: str
            Block name.
        num_inputs: int (optional)
            Number of input ports. (default = 2)
        signs: list[int] | array (1,) (optional)
            List of +1 or -1 coefficients (length = num_inputs). (default = all +1)

    Inputs:
        Dynamic — in1, in2, ..., inN. array (n,1)

    Outputs:
        out: array (n,1)
            Weighted sum of all inputs.
    """

    def __init__(self, name: str, num_inputs: int = 2, signs=None, sample_time:float|None = None):
        super().__init__(name, sample_time)

        # --- Validate num_inputs / signs -------------------------------------
        if signs is None and num_inputs == 0:
            raise ValueError(f"[{self.name}] Either 'num_inputs' or 'signs' must be provided.")

        if signs is None:
            signs = [1] * num_inputs

        if not isinstance(signs, (list, tuple, np.ndarray)):
            raise TypeError(f"[{self.name}] 'signs' must be a list, tuple or array.")

        if isinstance(signs, np.ndarray):
            if signs.ndim != 1:
                raise ValueError(f"[{self.name}] 'signs' array must be 1-dimensional.")
            signs = signs.tolist()

        if any(s not in (+1, -1) for s in signs):
            raise ValueError(f"[{self.name}] 'signs' must contain only +1 or -1.")

        if num_inputs == 0:
            num_inputs = len(signs)

        if len(signs) != num_inputs:
            raise ValueError(f"[{self.name}] len(signs) must equal num_inputs.")

        if num_inputs <= 0:
            raise ValueError(f"[{self.name}] num_inputs must be >= 1.")

        self.num_inputs = num_inputs
        self.signs = list(signs)

        # Create ports
        for i in range(num_inputs):
            self.inputs[f"in{i+1}"] = None

        self.outputs["out"] = None

    # ----------------------------------------------------------------------
    def initialize(self, t0: float):
        # If inputs already present, compute; else stay None
        ready = True
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

        if len(shapes) > 1:
            raise ValueError(f"[{self.name}] All inputs must have same dimension. Got sizes {shapes}.")

        self.outputs["out"] = self._compute_output()

    # ----------------------------------------------------------------------
    def state_update(self, t: float, dt: float):
        pass

    # ----------------------------------------------------------------------
    def _compute_output(self):
        total = None
        for i in range(self.num_inputs):
            u = np.asarray(self.inputs[f"in{i+1}"]).reshape(-1, 1)
            s = self.signs[i]

            if total is None:
                total = s * u
            else:
                total += s * u

        return total
