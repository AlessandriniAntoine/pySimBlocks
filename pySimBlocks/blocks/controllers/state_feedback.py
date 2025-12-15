import numpy as np
from pySimBlocks.core.block import Block


class StateFeedback(Block):
    """
    Discrete-time state-feedback controller.

    Description:
        Implements:
            u[k] = G * r[k] - K * x[k]

    Parameters:
        name: str
            Block name.
        K: matrix (m,n)
            State feedback gain.
        G: matrix (m,p)
            Reference feedforward gain. Default = zero matrix.
        sample_time: float | None (optional)
            Block sample time (default = None)

    Inputs:
        r: array (p,1)
            Reference vector.
        x: array (n,1)
            State measurement.

    Outputs:
        u: array (m,1)
            Control input.
    """


    def __init__(self, name: str, K: np.ndarray, G: np.ndarray, sample_time:float|None = None):
        super().__init__(name, sample_time)

        # Store matrices with validation
        self.K = np.asarray(K, dtype=float)
        self.G = np.asarray(G, dtype=float)

        m, n = self.K.shape
        m2, p = self.G.shape

        if m != m2:
            raise ValueError(
                f"Inconsistent dimensions: K is ({m},{n}), G is ({m2},{p})."
            )

        # Ports
        self.inputs["r"] = None
        self.inputs["x"] = None
        self.outputs["u"] = None

        # No state
        # (controller is static)

    # ---------------------------------------------------------
    # INITIALIZATION
    # ---------------------------------------------------------
    def initialize(self, t0: float):
        """
        If inputs are available at initialization, compute u.
        Otherwise, output remains None until first update.
        """
        r = self.inputs["r"]
        x = self.inputs["x"]

        if r is None or x is None:
            self.outputs["u"] = None
            return

        r = np.asarray(r).reshape(-1, 1)
        x = np.asarray(x).reshape(-1, 1)

        self.outputs["u"] = self.G @ r - self.K @ x

    # ---------------------------------------------------------
    # PHASE 1: OUTPUT UPDATE
    # ---------------------------------------------------------
    def output_update(self, t: float, dt: float):
        """
        Compute u = G*r - K*x
        """
        r = self.inputs["r"]
        x = self.inputs["x"]

        if r is None:
            raise RuntimeError(f"[{self.name}] Input 'r' is not connected or set.")
        if x is None:
            raise RuntimeError(f"[{self.name}] Input 'x' is not connected or set.")

        r = np.asarray(r).reshape(-1, 1)
        x = np.asarray(x).reshape(-1, 1)

        self.outputs["u"] = self.G @ r - self.K @ x

    # ---------------------------------------------------------
    # PHASE 2: STATE UPDATE
    # ---------------------------------------------------------
    def state_update(self, t: float, dt: float):
        """
        Static controller : no internal state.
        """
        pass
