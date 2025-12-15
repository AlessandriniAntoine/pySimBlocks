import numpy as np
from pySimBlocks.core.block_source import BlockSource


class Ramp(BlockSource):
    """
    Multi-dimensional ramp signal source.

    Description:
        Computes:
            out_i(t) = initial_output_i + slope_i * max(0, t - start_time_i)

    Parameters:
        name: str
            Block name.
        slope: float | array-like (n,) | array (n,1)
            Slope of each output dimension.
        start_time: float | array-like (n,) | array (n,1) (optional)
            Time at which each ramp starts. (default = 0.0).
        offset: float | array-like (n,) | array (n,1) (optional)
            Value before the ramp starts (default = zeros).
        sample_time: float | None (optional)
            Block sample time (default = None)

    Inputs:
        (none)

    Outputs:
        out: array (n,1)
            Ramp output vector.
    """

    def __init__(self, name, slope, start_time=0.0, offset=None, sample_time:float|None = None):
        super().__init__(name, sample_time)

        # --- Validate and normalize parameters ---
        S = self._to_column_vector("slope", np.asarray(slope))
        T = self._to_column_vector("start_time", np.asarray(start_time))

        if offset is None:
            O = np.zeros_like(S)
        else:
            O = self._to_column_vector("offset", np.asarray(offset))

        # Determine common dimension n
        dims = {S.shape[0], T.shape[0], O.shape[0]}
        dims.discard(1)  # scalar-like parameters are allowed
        if len(dims) > 1:
            raise ValueError(
                f"[{self.name}] Inconsistent dimensions among parameters "
                f"slope={S.shape}, start_time={T.shape}, offset={O.shape}."
            )
        n = max(S.shape[0], T.shape[0], O.shape[0])

        # Broadcast scalars into full vectors
        def expand(x):
            if x.shape[0] == 1:
                return np.full((n, 1), x.item(), dtype=float)
            return x.astype(float)

        self.slope = expand(S)
        self.start_time = expand(T)
        self.offset = expand(O)

        # Output port
        self.outputs["out"] = np.copy(self.offset)

    # ------------------------------------------------------------------
    def initialize(self, t0: float) -> None:
        self.outputs["out"] = np.copy(self.offset)

    # ------------------------------------------------------------------
    def output_update(self, t: float, dt: float) -> None:
        dt_vec = np.maximum(0.0, t - self.start_time)
        self.outputs["out"] = self.offset + self.slope * dt_vec
