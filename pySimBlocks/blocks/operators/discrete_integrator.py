import numpy as np
from pySimBlocks.core.block import Block


class DiscreteIntegrator(Block):
    """
    Discrete-time integrator.

    Description:
        Implements:
            x[k+1] = x[k] + dt * in[k]
            out[k] = x[k]

    Parameters:
        name: str
            Block name.
        initial_state: array (n,1) (optional)
            Initial state value.

    Inputs:
        in: array (n,1)
            Input signal to integrate.

    Outputs:
        out: array (n,1)
            Integrated state x[k].
    """


    def __init__(self, name: str, initial_state: np.ndarray | None = None):
        super().__init__(name)

        # One input port u[k]
        self.inputs["in"] = None

        # One output port y[k]
        self.outputs["out"] = None

        # Internal state x[k]
        if initial_state is not None:
            x0 = np.asarray(initial_state).reshape(-1, 1)
            self.state["x"] = x0.copy()
        else:
            # Dimension not known yet → initialized on first step
            self.state["x"] = None

        # Next state placeholder
        self.next_state["x"] = None

    # ------------------------------------------------------------------
    # INITIALIZATION
    # ------------------------------------------------------------------
    def initialize(self, t0: float):
        """
        Initialize x[0] and y[0].
        If no initial state and input is known, dimension is inferred.
        """
        x = self.state["x"]
        u = self.inputs["in"]

        if x is None:
            if u is not None:
                u = np.asarray(u).reshape(-1, 1)
                self.state["x"] = np.zeros_like(u)
            else:
                # output unknown until dimensions known
                self.outputs["out"] = None
                return

        self.outputs["out"] = self.state["x"].copy()
        self.next_state["x"] = self.state["x"].copy()

    # ------------------------------------------------------------------
    # PHASE 1 : OUTPUT UPDATE
    # ------------------------------------------------------------------
    def output_update(self, t: float):
        """
        y[k] = x[k]
        """
        x = self.state["x"]
        if x is None:
            raise RuntimeError(f"[{self.name}] State not initialized yet.")

        self.outputs["out"] = x.copy()

    # ------------------------------------------------------------------
    # PHASE 2 : STATE UPDATE
    # ------------------------------------------------------------------
    def state_update(self, t: float, dt: float):
        """
        x[k+1] = x[k] + dt * u[k]
        """
        u = self.inputs["in"]
        if u is None:
            raise RuntimeError(f"[{self.name}] Input 'in' not set.")

        u = np.asarray(u).reshape(-1, 1)

        x = self.state["x"]
        if x is None:
            # Late initialization
            x = np.zeros_like(u)

        self.next_state["x"] = x + dt * u
