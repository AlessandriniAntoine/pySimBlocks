import numpy as np
from pySimBlocks.core.block import Block


class Gain(Block):
    """
    Static gain block.

    Description:
        Computes:
            out = K * in

    Parameters:
        name: str
            Block name.
        gain: float | array-like (n,) | array (n,1)
            Gain scalar, vector, or matrix.

    Inputs:
        in: array (n,1)
            Input signal.

    Outputs:
        out: array (m,1)
            Output signal K * in.
    """

    def __init__(self, name: str, gain, sample_time:float|None = None):
        super().__init__(name, sample_time)

        # Normalize K into np.ndarray or scalar
        if np.isscalar(gain):
            self.K = gain
        else:
            self.K = np.asarray(gain)
            if self.K.ndim not in (1, 2):
                raise ValueError(
                    f"[{self.name}] Gain 'K' must be a scalar, vector (m,), or matrix (m,n). "
                    f"Got array with ndim={self.K.ndim}."
                )

        # One input port, one output port
        self.inputs["in"] = None
        self.outputs["out"] = None

    # ------------------------------------------------------------------
    # INITIALIZATION
    # ------------------------------------------------------------------
    def initialize(self, t0: float):
        """
        If input is already known at initialization, compute output.
        Otherwise, output is None until first propagation.
        """

        u = self.inputs["in"]
        if u is not None:
            u = np.asarray(u).reshape(-1, 1)
            self.outputs["out"] = self._compute(u)
        else:
            self.outputs["out"] = None

    # ------------------------------------------------------------------
    # PHASE 1 : OUTPUT UPDATE
    # ------------------------------------------------------------------
    def output_update(self, t: float, dt: float):
        """
        Compute y[k] = K * u[k].
        Inputs must be provided by the simulator before this call.
        """
        u = self.inputs["in"]
        if u is None:
            raise RuntimeError(f"[{self.name}] Input 'in' is not connected or not set.")

        u = np.asarray(u).reshape(-1, 1)
        self.outputs["out"] = self._compute(u)

    # ------------------------------------------------------------------
    # PHASE 2 : STATE UPDATE
    # ------------------------------------------------------------------
    def state_update(self, t: float, dt: float):
        """
        Gain has no internal state.
        """
        pass

    # ------------------------------------------------------------------
    # COMPUTATION
    # ------------------------------------------------------------------
    def _compute(self, u: np.ndarray) -> np.ndarray:

        # CASE 1: scalar gain
        if np.isscalar(self.K):
            return self.K * u

        # CASE 2: vector gain (m,)
        if self.K.ndim == 1:
            if u.shape != (1, 1):
                raise ValueError(
                    f"[{self.name}] Input 'in' must be shape (1,1) when gain 'K' is a vector (shape {self.K.shape}). "
                    f"Got input shape {u.shape}."
                )
            # Vector treated as row vector → output is (m,1)
            return self.K.reshape(-1, 1) * u[0, 0]

        # CASE 3: matrix gain (m,n)
        m, n = self.K.shape
        if u.shape[0] != n:
            raise ValueError(
                f"[{self.name}] Incompatible dimensions: K has shape {self.K.shape} "
                f"but input 'in' has shape {u.shape}."
            )

        return self.K @ u
