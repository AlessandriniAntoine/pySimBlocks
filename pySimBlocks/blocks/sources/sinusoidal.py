import numpy as np
from pySimBlocks.core.block_source import BlockSource


class Sinusoidal(BlockSource):
    """
    Multi-dimensional sinusoidal signal source block.

    Summary:
        Generates sinusoidal signals with configurable amplitude, frequency,
        phase and offset for each output dimension.

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

    I/O:
        Inputs:
            (none)
        Outputs:
            out : sinusoidal output signal.

    Notes:
        - The block has no internal state.
        - Parameters may be scalar or vector-valued.
        - Scalar parameters are broadcast to all output dimensions.
        - Each output dimension may have its own frequency and phase.
    """


    def __init__(self, name, amplitude, frequency, offset=0.0, phase=0.0, sample_time:float|None = None):
        super().__init__(name, sample_time)

        # Normalize parameters to column vectors
        A = self._to_column_vector("amplitude", np.asarray(amplitude))
        F = self._to_column_vector("frequency", np.asarray(frequency))
        O = self._to_column_vector("offset",    np.asarray(offset))
        P = self._to_column_vector("phase",     np.asarray(phase))

        # Determine final dimension n
        dims = {A.shape[0], F.shape[0], O.shape[0], P.shape[0]}
        dims.discard(1)
        if len(dims) > 1:
            raise ValueError(
                f"[{self.name}] Inconsistent parameter lengths: "
                f"amplitude={A.shape}, frequency={F.shape}, offset={O.shape}, phase={P.shape}"
            )
        n = max(A.shape[0], F.shape[0], O.shape[0], P.shape[0])

        # Broadcast scalar parameters to dimension n
        def expand(x):
            if x.shape[0] == 1:
                return np.full((n, 1), x.item(), dtype=float)
            return x.astype(float)

        self.amplitude = expand(A)
        self.frequency = expand(F)
        self.offset    = expand(O)
        self.phase     = expand(P)

        # Initialize output
        self.outputs["out"] = np.zeros((n, 1))

    # ------------------------------------------------------------------
    def _compute_output(self, t: float):
        self.outputs["out"] = (
            self.amplitude
            * np.sin(2 * np.pi * self.frequency * t + self.phase)
            + self.offset
        )

    # ------------------------------------------------------------------
    def initialize(self, t0: float) -> None:
        self._compute_output(t0)

    # ------------------------------------------------------------------
    def output_update(self, t: float, dt: float) -> None:
        self._compute_output(t)
