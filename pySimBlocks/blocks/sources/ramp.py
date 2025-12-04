import numpy as np
from pySimBlocks.core.block import Block

class Ramp(Block):
    """
    Multi-dimensional ramp signal source.

    Description:
        Computes:
            out_i(t) = initial_output_i + slope_i * max(0, t - start_time_i)

    Parameters:
        name: str
            Block name.
        slope: float | array (n,1)
            Slope of each output dimension.
        start_time: float | array (n,1)
            Time at which each ramp starts.
        initial_output: array (n,1) (optional)
            Value before the ramp starts (default = zeros).

    Inputs:
        (none)

    Outputs:
        out: array (n,1)
            Ramp output vector.
    """

    def __init__(
        self,
        name: str,
        slope,
        start_time=0.0,
        initial_output=None,
    ):
        super().__init__(name)

        # Prepare parameters to consistent (n,1) arrays
        self.slope, self.start_time, self.initial_output = \
            self._prepare_parameters(slope, start_time, initial_output)

        n = self.slope.shape[0]

        # Single output: n-dimensional vector
        self.outputs["out"] = np.copy(self.initial_output)


    @staticmethod
    def _to_array(x):
        x = np.asarray(x, dtype=float)
        if x.ndim == 0:
            return x.reshape(1,1)
        elif x.ndim == 1:
            return x.reshape(-1,1)
        elif x.ndim == 2 and x.shape[1] == 1:
            return x
        else:
            raise ValueError("Parameters must be scalar, 1D array, or (n,1) array.")


    @classmethod
    def _prepare_parameters(cls, slope, start_time, initial_output):
        # Convert to arrays
        S = cls._to_array(slope)
        T = cls._to_array(start_time)
        if initial_output is None:
            O = np.zeros_like(S)
        else:
            O = cls._to_array(initial_output)

        # Determine target dimension
        n = max(S.shape[0], T.shape[0], O.shape[0])

        def expand(x):
            if x.shape[0] == 1:
                return np.full((n,1), x.item(), dtype=float)
            if x.shape[0] == n:
                return x.astype(float)
            raise ValueError(f"Inconsistent size {x.shape[0]} with target dimension {n}.")

        return expand(S), expand(T), expand(O)


    def initialize(self, t0: float) -> None:
        self.outputs["out"] = np.copy(self.initial_output)


    def output_update(self, t: float) -> None:
        dt_vec = np.maximum(0.0, t - self.start_time)
        self.outputs["out"] = self.initial_output + self.slope * dt_vec


    def state_update(self, t: float, dt: float) -> None:
        pass
