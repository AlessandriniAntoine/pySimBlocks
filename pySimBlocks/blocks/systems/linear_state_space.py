import numpy as np
from pySimBlocks.core.block import Block


class LinearStateSpace(Block):
    """
    Discrete-time linear state-space system.

    Description:
        Implements:
            x[k+1] = A x[k] + B u[k]
            y[k]   = C x[k]
        Currently no matrix D to avoid algebric loop

    Parameters:
        name: str
            Block name.
        A: matrix (n,n)
            State transition matrix.
        B: matrix (n,m)
            Input matrix.
        C: matrix (p,n)
            Output matrix.
        x0: array (n,1) (optional)
            Initial state vector (default = zeros).

    Inputs:
        u: array (m,1)
            Input vector u[k].

    Outputs:
        x: array (n,1)
            Current state vector x[k].
        y: array (p,1)
            Output vector y[k].
    """
    direct_feedthrough = False

    def __init__(
        self,
        name: str,
        A: np.ndarray,
        B: np.ndarray,
        C: np.ndarray,
        x0: np.ndarray | None = None,
    ):
        super().__init__(name)

        # ------------------------------------------------------------------
        # Store and check matrices
        # ------------------------------------------------------------------
        self.A = np.asarray(A)
        self.B = np.asarray(B)
        self.C = np.asarray(C)

        n = self.A.shape[0]

        if self.A.shape != (n, n):
            raise ValueError("A must be square (n x n).")

        if self.B.shape[0] != n:
            raise ValueError("B must have the same number of rows as A.")

        if self.C.shape[1] != n:
            raise ValueError("C must have the same number of columns as A.")

        # ------------------------------------------------------------------
        # Initial state x0
        # ------------------------------------------------------------------
        if x0 is None:
            x0 = np.zeros((n, 1))
        else:
            x0 = np.asarray(x0).reshape(-1, 1)
            if x0.shape != (n, 1):
                raise ValueError(f"x0 must have shape ({n}, 1).")

        self.state["x"] = x0
        self.next_state["x"] = x0.copy()

        # ------------------------------------------------------------------
        # Ports
        # ------------------------------------------------------------------
        # Single input "u" (m,1). Value is provided by the simulator.
        self.inputs["u"] = None

        # Single output "y" (p,1)
        self.outputs["y"] = None
        self.outputs["x"] = None

    # ----------------------------------------------------------------------
    # INITIALIZATION
    # ----------------------------------------------------------------------
    def initialize(self, t0: float) -> None:
        """
        Compute initial output y[0] from x[0] and (if available) u[0].

        If u is not yet known at initialization, we assume u[0] = 0
        for the initial output (but NOT for the subsequent steps).
        """
        x = self.state["x"]
        self.outputs["y"] = self.C @ x

        # Keep next_state consistent (no state change at t0)
        self.outputs["x"] = x.copy()
        self.next_state["x"] = x.copy()

    # ----------------------------------------------------------------------
    # PHASE 1 : OUTPUT UPDATE
    # ----------------------------------------------------------------------
    def output_update(self, t: float) -> None:
        """
        Compute y[k] = C x[k] from current state and input.
        """
        x = self.state["x"]

        self.outputs["y"] = self.C @ x
        self.outputs["x"] = x.copy()

    # ----------------------------------------------------------------------
    # PHASE 2 : STATE UPDATE
    # ----------------------------------------------------------------------
    def state_update(self, t: float, dt: float) -> None:
        """
        Compute x[k+1] = A x[k] + B u[k].
        """
        u = self.inputs["u"]
        if u is None:
            raise RuntimeError(f"[{self.name}] Input 'u' is not connected or not set.")

        u = np.asarray(u).reshape(self.B.shape[1], 1)
        x = self.state["x"]

        self.next_state["x"] = self.A @ x + self.B @ u
