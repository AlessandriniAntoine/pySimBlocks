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
        num_inputs: int
            Number of input ports.
        signs: list[int]
            List of +1 or -1 coefficients (length = num_inputs).

    Inputs:
        Dynamic — in1, in2, ..., inN. array (n,1)

    Outputs:
        out: array (n,1)
            Weighted sum of all inputs.
    """

    def __init__(self, name: str,
                 num_inputs: int = 0,
                 signs=None):

        super().__init__(name)

        if signs is None and num_inputs == 0:
            raise ValueError("Either 'num_inputs' or 'signs' must be provided.")

        if num_inputs == 0:
            num_inputs = len(signs)

        if signs is None:
            signs = [1] * num_inputs

        if len(signs) != num_inputs:
            raise ValueError("Length of 'signs' must match num_inputs.")

        # port names: in1, in2, ..., inN
        self.num_inputs = num_inputs
        self.signs = signs

        for i in range(num_inputs):
            self.inputs[f"in{i+1}"] = None

        # one output
        self.outputs["out"] = None

    # ------------------------------------------------------------------
    # INITIALIZATION
    # ------------------------------------------------------------------
    def initialize(self, t0: float):
        """
        If all inputs are already defined, compute output.
        Otherwise output stays None until first real step.
        """

        # Check if all inputs exist
        for i in range(self.num_inputs):
            if self.inputs[f"in{i+1}"] is None:
                self.outputs["out"] = None
                return

        # Compute initial sum
        self.outputs["out"] = self._compute_output()

    # ------------------------------------------------------------------
    # PHASE 1 : OUTPUT UPDATE
    # ------------------------------------------------------------------
    def output_update(self, t: float):
        """
        Compute y[k] = Σ s_i * u_i[k]
        """
        # Make sure all inputs are available
        for i in range(self.num_inputs):
            u = self.inputs[f"in{i+1}"]
            if u is None:
                raise RuntimeError(
                    f"[{self.name}] Input 'in{i+1}' is not connected or not set."
                )

        self.outputs["out"] = self._compute_output()

    # ------------------------------------------------------------------
    # PHASE 2 : STATE UPDATE
    # ------------------------------------------------------------------
    def state_update(self, t: float, dt: float):
        """
        Sum block has no state.
        """
        pass

    # ------------------------------------------------------------------
    # INTERNAL
    # ------------------------------------------------------------------
    def _compute_output(self) -> np.ndarray:
        """
        Compute Σ s_i * u_i as an (n,1) numpy array.
        """
        total = None

        for i in range(self.num_inputs):
            u = np.asarray(self.inputs[f"in{i+1}"]).reshape(-1, 1)
            s = self.signs[i]

            if total is None:
                total = s * u
            else:
                total += s * u

        return total
