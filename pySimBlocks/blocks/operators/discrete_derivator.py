import numpy as np
from pySimBlocks.core.block import Block


class DiscreteDerivator(Block):
    """
    Discrete-time differentiator.

    Description:
        Definitions:
            y[k] = (u[k+1] - u[k]) / dt

    Parameters:
        name: str
            Block name.

    Inputs:
        in: array (n,1)
            Input signal u[k].

    Outputs:
        out: array (n,1)
            Estimated derivative y[k].
    """

    def __init__(
        self,
        name: str,
    ):
        super().__init__(name)

        # Ports
        self.inputs["in"] = None
        self.outputs["out"] = None

        # Internal state: previous input u[k-1]
        self.state["u_prev"] = None
        self.next_state["u_prev"] = None

        # Store dt after each state_update
        self._dt = 1.0

    # ------------------------------------------------------------------
    # INITIALIZATION
    # ------------------------------------------------------------------
    def initialize(self, t0: float):
        """
        Initialize u_prev and output.
        y[0] = 0 by definition.
        """
        self._dt = 1.0  # safe default before first state_update

        u = self.inputs["in"]
        if u is not None:
            u = np.asarray(u).reshape(-1, 1)
            self.state["u_prev"] = u.copy()
        else:
            self.state["u_prev"] = None

        # Derivative at first sample = zero
        self.outputs["out"] = np.zeros_like(u) if u is not None else None
        self.next_state["u_prev"] = self.state["u_prev"]

    # ------------------------------------------------------------------
    # PHASE 1 : OUTPUT UPDATE
    # ------------------------------------------------------------------
    def output_update(self, t: float):
        """
        Compute y[k] based on:
            u[k] and u[k-1]
        """
        u = self.inputs["in"]
        if u is None:
            raise RuntimeError(f"[{self.name}] Input 'in' not set.")

        u = np.asarray(u).reshape(-1, 1)
        u_prev = self.state["u_prev"]

        # If no previous input → derivative undefined, return 0
        if u_prev is None:
            self.outputs["out"] = np.zeros_like(u)
            return

        y = (u - u_prev) / self._dt

        self.outputs["out"] = y

    # ------------------------------------------------------------------
    # PHASE 2 : STATE UPDATE
    # ------------------------------------------------------------------
    def state_update(self, t: float, dt: float):
        """
        Update stored input:
            u_prev[k+1] = u[k]
        """
        u = self.inputs["in"]
        if u is None:
            raise RuntimeError(f"[{self.name}] Input 'in' not set.")

        self._dt = dt
        u = np.asarray(u).reshape(-1, 1)

        self.next_state["u_prev"] = u.copy()
