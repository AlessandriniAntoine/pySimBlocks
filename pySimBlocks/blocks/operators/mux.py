import numpy as np
from pySimBlocks.core.block import Block


class Mux(Block):
    """
    Vertical signal concatenation block.

    Summary:
        Concatenates multiple input column vectors vertically into a single
        column vector.

    Parameters (overview):
        num_inputs : int
            Number of input ports to concatenate.
        sample_time : float, optional
            Block execution period.

    I/O:
        Inputs:
            in1, in2, ..., inN : column vectors
                Defined dynamically by `num_inputs`.
        Outputs:
            out : concatenated column vector.

    Notes:
        - Stateless block.
        - Direct feedthrough.
        - Input vectors are concatenated vertically without dimension matching
          constraints between inputs.
    """


    def __init__(self, name: str, num_inputs: int = 2, sample_time:float|None = None):
        super().__init__(name, sample_time)

        if not isinstance(num_inputs, int) or num_inputs < 1:
            raise ValueError(f"[{self.name}] num_inputs must be a positive integer.")

        self.num_inputs = num_inputs

        # Create dynamic input ports: in1, in2, ..., inN
        for i in range(num_inputs):
            self.inputs[f"in{i+1}"] = None

        # Single output
        self.outputs["out"] = None

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
    def output_update(self, t: float, dt: float):
        """
        Compute vertical concatenation of all inputs.
        """

        self.outputs["out"] = self._compute_output()

    # ---------------------------------------------------------
    def state_update(self, t: float, dt: float):
        pass


    # ---------------------------------------------------------
    def _compute_output(self) -> np.ndarray:
        """
        Helper method to compute the vertical concatenation of all inputs.
        Used during initialization.
        """
        vectors = []

        for i in range(self.num_inputs):
            u = self.inputs[f"in{i+1}"]

            if u is None:
                raise RuntimeError(
                    f"[{self.name}] Input 'in{i+1}' is not connected or not set."
                )

            u = np.asarray(u)

            # Strict dimensional validation
            if u.ndim != 2 or u.shape[1] != 1:
                raise ValueError(
                    f"[{self.name}] Input 'in{i+1}' must be a column vector (n,1). "
                    f"Got shape {u.shape}."
                )

            vectors.append(u)

        return np.vstack(vectors)
