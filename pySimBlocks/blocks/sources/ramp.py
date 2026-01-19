import numpy as np
from numpy.typing import ArrayLike
from pySimBlocks.core.block_source import BlockSource


class Ramp(BlockSource):
    """
    Multi-dimensional ramp signal source block (Option B).

    Summary:
        Generates a ramp signal element-wise on a 2D output array:
            y(t) = offset + slope * max(0, t - start_time)

        Parameters may be scalars, vectors, or matrices. Only scalar-to-shape
        broadcasting is allowed; all non-scalar parameters must share the same
        shape.

    Parameters (overview):
        slope : float or array-like
            Ramp slope. Scalar -> broadcast; otherwise fixes output shape.
        start_time : float or array-like, optional
            Ramp start time. Scalar -> broadcast; otherwise must match output shape.
        offset : float or array-like, optional
            Output value before the ramp starts. Scalar -> broadcast; otherwise must match output shape.
        sample_time : float, optional
            Block execution period.

    Outputs:
        out : ramp output signal (2D ndarray)

    Notes:
        - Stateless block.
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
        slope: ArrayLike,
        start_time: ArrayLike = 0.0,
        offset: ArrayLike | None = None,
        sample_time: float | None = None,
    ):
        super().__init__(name, sample_time)

        S = self._to_2d_array("slope", slope, dtype=float)
        T = self._to_2d_array("start_time", start_time, dtype=float)

        if offset is None:
            O = np.array([[0.0]], dtype=float)  # scalar, will be broadcast if needed
        else:
            O = self._to_2d_array("offset", offset, dtype=float)

        # Resolve common shape using strict scalar-only broadcasting policy
        target_shape = self._resolve_common_shape({"slope": S, "start_time": T, "offset": O})

        self.slope = self._broadcast_scalar_only("slope", S, target_shape)
        self.start_time = self._broadcast_scalar_only("start_time", T, target_shape)
        self.offset = self._broadcast_scalar_only("offset", O, target_shape)

        # Output port
        self.outputs["out"] = self.offset.copy()

    # ------------------------------------------------------------------
    def initialize(self, t0: float) -> None:
        self.outputs["out"] = self.offset.copy()

    # ------------------------------------------------------------------
    def output_update(self, t: float, dt: float) -> None:
        # Element-wise time shift
        dt_mat = np.maximum(0.0, t - self.start_time)
        self.outputs["out"] = self.offset + self.slope * dt_mat
