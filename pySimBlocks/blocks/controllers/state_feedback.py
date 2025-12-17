import numpy as np
from pySimBlocks.core.block import Block


class StateFeedback(Block):
    """
    Discrete-time state-feedback controller block.

    Summary:
        Implements a static discrete-time state-feedback control law
        combining reference feedforward and state feedback.

    Parameters (overview):
        K : array-like
            State feedback gain matrix.
        G : array-like
            Reference feedforward gain matrix.
        sample_time : float, optional
            Block execution period.

    I/O:
        Inputs:
            r : reference vector.
            x : state measurement vector.
        Outputs:
            u : control input vector.

    Notes:
        - The controller is static and has no internal state.
        - The control law is evaluated at each simulation step.
        - Both reference and state inputs must be connected.
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
