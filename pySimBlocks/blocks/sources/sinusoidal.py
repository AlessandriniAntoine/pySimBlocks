import numpy as np
from pySimBlocks.core.block_source import BlockSource


class Sinusoidal(BlockSource):
    """
    Multi-dimensional sinusoidal signal source.

    Description:
        Computes:
            out_i(t) = A_i * sin(2π f_i t + φ_i) + offset_i

    Parameters:
        name: str
            Block name.
        amplitude: float | array-like (n,) | array (n,1)
            Amplitude A_i.
        frequency: float | array-like (n,) | array (n,1)
            Frequency f_i (Hz).
        offset: float | array-like (n,) | array (n,1) (optional)
            Offset added to each output. (default = 0.0)
        phase: float | array-like (n,) | array (n,1) (optional)
            Phase shift φ_i (rad). (default = 0.0)

    Inputs:
        (none)

    Outputs:
        out: array (n,1)
            Sinusoidal output vector.
    """

    def __init__(self, name, amplitude, frequency, offset=0.0, phase=0.0):
        super().__init__(name)

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
    def output_update(self, t: float) -> None:
        self._compute_output(t)
