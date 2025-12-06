import numpy as np
from pySimBlocks.core.block_source import BlockSource


class WhiteNoise(BlockSource):
    """
    Multi-dimensional Gaussian noise source.

    Description:
        Computes:
            out_i(t) ~ N(mean_i, std_i^2)

    Parameters:
        name: str
            Block name.
        mean: float | array-like (n,) | array (n,1) (optional)
            Mean value for each dimension. (default = 0.0)
        std: float | array-like (n,) | array (n,1) (optional)
            Standard deviation for each dimension. Must be >= 0. (default = 1.0)
        seed: int (optional)
            Random seed for reproducibility. (default = None)

    Inputs:
        (none)

    Outputs:
        out: array (n,1)
            Noise vector drawn at each output_update().
    """

    def __init__(self, name: str, mean=0.0, std=1.0, seed:int | None=None):
        super().__init__(name)

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
    def output_update(self, t: float) -> None:
        # Draw new noise sample
        self.outputs["out"] = self.mean + self.std * self.rng.standard_normal(self.mean.shape)
