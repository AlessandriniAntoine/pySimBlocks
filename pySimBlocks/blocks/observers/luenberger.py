import numpy as np
from pySimBlocks.core.block import Block


class Luenberger(Block):
    """
    Discrete-time Luenberger state observer.

    Description:
        Implements:
            x_hat[k+1] = A x_hat[k] + B u[k] + L * (y[k] - C x_hat[k])
            y_hat[k]   = C x_hat[k]
        Currently no matrix D to avoid algebric loop

    Parameters:
        name: str
            Block name.
        A: matrix (n,n)
            System state matrix.
        B: matrix (n,m)
            Input matrix.
        C: matrix (p,n)
            Output matrix.
        L: matrix (n,p)
            Observer gain matrix.
        x0: array (n,1) (optional)
            Initial estimated state (default = zeros).
        sample_time: float | None (optional)
                Block sample time (default = None)

    Inputs:
        u: array (m,1)
            Control input.
        y: array (p,1)
            System output measurement.

    Outputs:
        x_hat: array (n,1)
            State estimate.
        y_hat: array (p,1)
            Estimated output C x̂[k] + D u[k].
    """

    direct_feedthrough = False

    def __init__(
        self,
        name: str,
        A: np.ndarray,
        B: np.ndarray,
        C: np.ndarray,
        L: np.ndarray,
        x0: np.ndarray | None = None,
        sample_time:float|None = None
    ):
        super().__init__(name, sample_time)

        # ------------------------------------------------------------------
        # Store and check matrices
        # ------------------------------------------------------------------
        self.A = np.asarray(A)
        self.B = np.asarray(B)
        self.C = np.asarray(C)
        self.L = np.asarray(L)

        n = self.A.shape[0]

        if self.A.shape != (n, n):
            raise ValueError("A must be square (n x n).")

        if self.B.shape[0] != n:
            raise ValueError("B must have the same number of rows as A.")

        if self.C.shape[1] != n:
            raise ValueError("C must have the same number of columns as A.")

        if self.L.shape[0] != n:
            raise ValueError("L must have the same number of rows as A.")

        if self.L.shape[1] != self.C.shape[0]:
            raise ValueError("L must have the same number of columns as rows of C.")

        # ------------------------------------------------------------------
        # Initial state x0
        # ------------------------------------------------------------------
        if x0 is None:
            x0 = np.zeros((n, 1))
        else:
            x0 = np.asarray(x0).reshape(-1, 1)
            if x0.shape != (n, 1):
                raise ValueError(f"x0 must have shape ({n}, 1).")

        self.state["x_hat"] = x0
        self.next_state["x_hat"] = x0.copy()

        # ------------------------------------------------------------------
        # Ports
        # ------------------------------------------------------------------
        # Single input "u" (m,1). Value is provided by the simulator.
        self.inputs["u"] = None
        self.inputs["y"] = None

        # Single output "y" (p,1)
        self.outputs["y_hat"] = None
        self.outputs["x_hat"] = None

    # ----------------------------------------------------------------------
    # INITIALIZATION
    # ----------------------------------------------------------------------
    def initialize(self, t0: float) -> None:
        """
        Compute initial output y[0] from x[0] and (if available) u[0].

        If u is not yet known at initialization, we assume u[0] = 0
        for the initial output (but NOT for the subsequent steps).
        """
        x_hat = self.state["x_hat"]
        self.outputs["y_hat"] = self.C @ x_hat

        # Keep next_state consistent (no state change at t0)
        self.outputs["x_hat"] = x_hat.copy()
        self.next_state["x_hat"] = x_hat.copy()

    # ----------------------------------------------------------------------
    # PHASE 1 : OUTPUT UPDATE
    # ----------------------------------------------------------------------
    def output_update(self, t: float, dt: float) -> None:
        """
        Compute y[k] = C x[k] + D u[k] from current state and input.
        """
        x_hat = self.state["x_hat"]

        self.outputs["y_hat"] = self.C @ x_hat
        self.outputs["x_hat"] = x_hat.copy()

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
        y = self.inputs["y"]
        if y is None:
            raise RuntimeError(f"[{self.name}] Input 'y' is not connected or not set.")

        u = np.asarray(u).reshape(self.B.shape[1], 1)
        y = np.asarray(y).reshape(self.C.shape[0], 1)
        x_hat = self.state["x_hat"]
        y_hat = self.C @ x_hat

        self.next_state["x_hat"] = self.A @ x_hat + self.B @ u + self.L @ (y - y_hat)
