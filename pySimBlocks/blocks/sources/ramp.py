import numpy as np
from pySimBlocks.core.block_source import BlockSource


class Ramp(BlockSource):
    """
    Multi-dimensional ramp signal source block.

    Summary:
        Generates a ramp signal for each output dimension, starting at a given
        time with a specified slope and initial offset.

    Parameters (overview):
        slope : float or array-like
            Ramp slope for each output dimension.
        start_time : float or array-like, optional
            Time at which the ramp starts.
        offset : float or array-like, optional
            Output value before the ramp starts.
        sample_time : float, optional
            Block execution period.

    I/O:
        Inputs:
            (none)
        Outputs:
            out : ramp output signal.

    Notes:
        - The block has no internal state.
        - Parameters may be scalar or vector-valued.
        - Scalar parameters are broadcast to all output dimensions.
        - Each output dimension may have a different slope and start time.
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
