import numpy as np
from pySimBlocks.core.block import Block


class Mux(Block):
    """
    Vertical signal concatenation (Mux).

    Description:
        Concatenates multiple input signals into a single output vector:

            out = [in1;
                   in2;
                   ...
                   inN]

        All inputs are column vectors (ni, 1) and the output is the vertical
        concatenation of all of them, i.e. shape (sum_i ni, 1).

    Parameters:
        name: str
            Block name.
        num_inputs: int
            Number of input ports to create.

    Inputs:
        Dynamic — in1, in2, ..., inN. array (n,1)

    Outputs:
        out: array (sum_i ni, 1)
            Vertical concatenation of all inputs.

    Notes:
        - If input_sizes is provided, each input is dimension-checked.
        - If omitted, dimensions are inferred at first step.
        - Mux has no internal state.
    """

    def __init__(self, name: str, num_inputs: int = 2):
        super().__init__(name)

        if num_inputs < 1:
            raise ValueError("num_inputs must be >= 1.")

        self.num_inputs = num_inputs

        # Create input ports: in1, in2, ..., inN
        for i in range(num_inputs):
            self.inputs[f"in{i+1}"] = None

        # Single output
        self.outputs["out"] = None

    # ---------------------------------------------------------
    # INITIALIZATION
    # ---------------------------------------------------------
    def initialize(self, t0: float):
        """
        If all inputs are available, concatenate them.
        Otherwise output remains None until first update.
        """
        for i in range(self.num_inputs):
            if self.inputs[f"in{i+1}"] is None:
                self.outputs["out"] = None
                return

        self.outputs["out"] = self._compute_output()

    # ---------------------------------------------------------
    # PHASE 1: OUTPUT UPDATE
    # ---------------------------------------------------------
    def output_update(self, t: float):
        """
        Compute y = vertcat(inputs).
        """
        for i in range(self.num_inputs):
            if self.inputs[f"in{i+1}"] is None:
                raise RuntimeError(
                    f"[{self.name}] Input 'in{i+1}' is not connected or not set."
                )

        self.outputs["out"] = self._compute_output()

    # ---------------------------------------------------------
    # PHASE 2: STATE UPDATE
    # ---------------------------------------------------------
    def state_update(self, t: float, dt: float):
        """
        Mux has no internal state.
        """
        pass

    # ---------------------------------------------------------
    # INTERNAL
    # ---------------------------------------------------------
    def _compute_output(self) -> np.ndarray:
        """
        Concatenate inputs vertically.
        """
        vectors = []

        for i in range(self.num_inputs):
            u = np.asarray(self.inputs[f"in{i+1}"]).reshape(-1, 1)
            vectors.append(u)

        return np.vstack(vectors)
