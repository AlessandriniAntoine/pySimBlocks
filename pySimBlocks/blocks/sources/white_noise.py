import numpy as np
from numpy.typing import ArrayLike
from pySimBlocks.core.block_source import BlockSource


class WhiteNoise(BlockSource):
    """
    Multi-dimensional Gaussian white noise source block (Option B).

    Summary:
        Generates independent Gaussian noise samples at each simulation step,
        element-wise on a 2D output array:
            y = mean + std * N(0,1)

        Parameters may be scalars, vectors, or matrices. Only scalar-to-shape
        broadcasting is allowed; all non-scalar parameters must share the same
        shape.

    Parameters (overview):
        mean : float or array-like, optional
            Mean value of the noise.
        std : float or array-like, optional
            Standard deviation of the noise (must be >= 0 element-wise).
        seed : int, optional
            Random seed for reproducibility.
        sample_time : float, optional
            Block execution period.

    Outputs:
        out : noise output signal (2D ndarray)

    Notes:
        - Stateless (but uses an internal RNG).
        - Normalization:
            scalar -> (1,1), 1D -> (n,1), 2D -> (m,n)
        - Broadcasting:
            Only (1,1) scalars are broadcast to the common shape.
            No NumPy broadcasting beyond that.
        - No implicit flattening is performed.
    """

    def __init__(
        self,
        name: str,
        mean: ArrayLike = 0.0,
        std: ArrayLike = 1.0,
        seed: int | None = None,
        sample_time: float | None = None,
    ):
        super().__init__(name, sample_time)

        M = self._to_2d_array("mean", mean, dtype=float)
        S = self._to_2d_array("std", std, dtype=float)

        target_shape = self._resolve_common_shape({
            "mean": M,
            "std": S,
        })

        self.mean = self._broadcast_scalar_only("mean", M, target_shape)
        self.std = self._broadcast_scalar_only("std", S, target_shape)

        # Validate std >= 0 element-wise
        if np.any(self.std < 0.0):
            raise ValueError(f"[{self.name}] std must be >= 0 (element-wise).")

        self.rng = np.random.default_rng(seed)

        self.outputs["out"] = np.zeros(target_shape, dtype=float)

    # ------------------------------------------------------------------
    def _draw(self) -> np.ndarray:
        return self.mean + self.std * self.rng.standard_normal(self.mean.shape)

    # ------------------------------------------------------------------
    def initialize(self, t0: float) -> None:
        self.outputs["out"] = self._draw()

    # ------------------------------------------------------------------
    def output_update(self, t: float, dt: float) -> None:
        self.outputs["out"] = self._draw()
