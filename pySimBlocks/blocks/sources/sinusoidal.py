import numpy as np
from numpy.typing import ArrayLike
from pySimBlocks.core.block_source import BlockSource


class Sinusoidal(BlockSource):
    """
    Multi-dimensional sinusoidal signal source block (Option B).

    Summary:
        Generates sinusoidal signals element-wise on a 2D output array:
            y(t) = amplitude * sin(2*pi*frequency*t + phase) + offset

        Parameters may be scalars, vectors, or matrices. Only scalar-to-shape
        broadcasting is allowed; all non-scalar parameters must share the same
        shape.

    Parameters (overview):
        amplitude : float or array-like
            Sinusoidal amplitude.
        frequency : float or array-like
            Sinusoidal frequency in Hertz.
        phase : float or array-like, optional
            Phase shift in radians.
        offset : float or array-like, optional
            Constant offset added to the signal.
        sample_time : float, optional
            Block execution period.

    Outputs:
        out : sinusoidal output signal (2D ndarray)

    Notes:
        - Stateless.
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
        amplitude: ArrayLike,
        frequency: ArrayLike,
        offset: ArrayLike = 0.0,
        phase: ArrayLike = 0.0,
        sample_time: float | None = None,
    ):
        super().__init__(name, sample_time)

        A = self._to_2d_array("amplitude", amplitude, dtype=float)
        F = self._to_2d_array("frequency", frequency, dtype=float)
        O = self._to_2d_array("offset", offset, dtype=float)
        P = self._to_2d_array("phase", phase, dtype=float)

        target_shape = self._resolve_common_shape({
            "amplitude": A,
            "frequency": F,
            "offset": O,
            "phase": P,
        })

        self.amplitude = self._broadcast_scalar_only("amplitude", A, target_shape)
        self.frequency = self._broadcast_scalar_only("frequency", F, target_shape)
        self.offset = self._broadcast_scalar_only("offset", O, target_shape)
        self.phase = self._broadcast_scalar_only("phase", P, target_shape)

        self.outputs["out"] = np.zeros(target_shape, dtype=float)

    # ------------------------------------------------------------------
    def _compute_output(self, t: float) -> None:
        self.outputs["out"] = (
            self.amplitude
            * np.sin(2.0 * np.pi * self.frequency * t + self.phase)
            + self.offset
        )

    # ------------------------------------------------------------------
    def initialize(self, t0: float) -> None:
        self._compute_output(t0)

    # ------------------------------------------------------------------
    def output_update(self, t: float, dt: float) -> None:
        self._compute_output(t)
