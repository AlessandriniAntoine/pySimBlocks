import numpy as np
from pySimBlocks.core.block_source import BlockSource


class WhiteNoise(BlockSource):
    """
    Multi-dimensional Gaussian white noise source block.

    Summary:
        Generates independent Gaussian noise samples at each simulation step
        for each output dimension.

    Parameters (overview):
        mean : float or array-like, optional
            Mean value of the noise.
        std : float or array-like, optional
            Standard deviation of the noise.
        seed : int, optional
            Random seed for reproducibility.
        sample_time : float, optional
            Block execution period.

    I/O:
        Inputs:
            (none)
        Outputs:
            out : noise output signal.

    Notes:
        - The block has no internal state.
        - Noise samples are drawn independently at each step.
        - Parameters may be scalar or vector-valued.
        - Scalar parameters are broadcast to all output dimensions.
    """


    def __init__(self, name: str, mean=0.0, std=1.0, seed:int | None=None, sample_time:float|None = None):
        super().__init__(name, sample_time)

        # Normalize parameters
        M = self._to_column_vector("mean", np.asarray(mean))
        S = self._to_column_vector("std",  np.asarray(std))

        # Validate std ≥ 0
        if np.any(S < 0):
            raise ValueError(f"[{self.name}] std must be >= 0.")


        # Determine final dimension n
        dims = {M.shape[0], S.shape[0]}
        dims.discard(1)
        if len(dims) > 1:
            raise ValueError(
                f"[{self.name}] Inconsistent parameter lengths: "
                f"mean={M.shape}, std={S.shape}"
            )

        n = max(M.shape[0], S.shape[0])


        # Broadcast scalars
        def expand(x):
            if x.shape[0] == 1:
                return np.full((n, 1), x.item(), dtype=float)
            return x.astype(float)

        self.mean = expand(M)
        self.std = expand(S)

        # Random generator
        self.rng = np.random.default_rng(seed)

        # Initial output
        self.outputs["out"] = np.zeros((n, 1))

    # ------------------------------------------------------------------
    def initialize(self, t0: float) -> None:
        # Draw noise at t0
        self.outputs["out"] = self.mean + self.std * self.rng.standard_normal(self.mean.shape)

    # ------------------------------------------------------------------
    def output_update(self, t: float, dt: float) -> None:
        # Draw new noise sample
        self.outputs["out"] = self.mean + self.std * self.rng.standard_normal(self.mean.shape)
