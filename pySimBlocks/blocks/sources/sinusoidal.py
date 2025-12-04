import numpy as np
from pySimBlocks.core.block import Block


class Sinusoidal(Block):
    """
    Multi-dimensional sinusoidal signal source.

    Description:
        Computes:
            out_i(t) = A_i * sin(2π f_i t + φ_i) + offset_i

    Parameters:
        name: str
            Block name.
        amplitude: float | array (n,1)
            Amplitude A_i of each sinusoid.
        frequency: float | array (n,1)
            Frequency f_i of each sinusoid (Hz).
        offset: float | array (n,1)
            Offset added to each output.
        phase: float | array (n,1)
            Phase shift φ_i (rad).

    Inputs:
        (none)

    Outputs:
        out: array (n,1)
            Sinusoidal output vector.
    """

    def __init__(
        self,
        name: str,
        amplitude,
        frequency,
        offset=0.0,
        phase=0.0,
    ):
        super().__init__(name)

        # Convert and broadcast parameters to shape (n, 1)
        self.amplitude, self.frequency, self.offset, self.phase = \
            self._prepare_parameters(amplitude, frequency, offset, phase)

        # single output port: "out" (n x 1)
        n = self.amplitude.shape[0]
        self.outputs["out"] = np.zeros((n, 1))

    @staticmethod
    def _prepare_parameters(amplitude, frequency, offset, phase):
        """
        Take amplitude, frequency, offset, phase as scalars or 1D arrays
        and return four arrays of shape (n, 1) with consistent length n.
        """

        def _to_array(x):
            x = np.asarray(x, dtype=float)
            if x.ndim == 0:
                return x.reshape(1, 1)  # scalar -> (1,1)
            elif x.ndim == 1:
                return x.reshape(-1, 1) # (n,) -> (n,1)
            elif x.ndim == 2 and x.shape[1] == 1:
                return x
            else:
                raise ValueError("Parameters must be scalar, 1D array, or (n,1) array.")

        A = _to_array(amplitude)
        F = _to_array(frequency)
        O = _to_array(offset)
        P = _to_array(phase)

        # determine target dimension n
        sizes = [A.shape[0], F.shape[0], O.shape[0], P.shape[0]]
        n = max(sizes)

        def _expand(x):
            if x.shape[0] == 1:
                # broadcast scalar to length n
                return np.full((n, 1), x.item(), dtype=float)
            if x.shape[0] == n:
                return x.astype(float)
            raise ValueError(
                f"Inconsistent parameter size {x.shape[0]} with target dimension {n}."
            )

        A = _expand(A)
        F = _expand(F)
        O = _expand(O)
        P = _expand(P)

        return A, F, O, P

    def _compute_output(self, t: float):
        """
        Compute out(t) = A * sin(2 pi f t + phi) + offset
        with A, f, phi, offset of shape (n, 1).
        """
        self.outputs["out"] = (
            self.amplitude * np.sin(2.0 * np.pi * self.frequency * t + self.phase)
            + self.offset
        )


    def initialize(self, t0: float) -> None:
        self._compute_output(t0)


    def output_update(self, t: float) -> None:
        self._compute_output(t)


    def state_update(self, t: float, dt: float) -> None:
        # self._compute_output(t)
        pass
