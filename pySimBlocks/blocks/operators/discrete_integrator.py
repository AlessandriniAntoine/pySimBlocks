import numpy as np
from pySimBlocks.core.block import Block


class DiscreteIntegrator(Block):
    """
    Discrete-time integrator.

    Description:
        Implements:
            x[k+1] = x[k] + dt * in[k]
            out[k] = x[k]

        Supported integration method:
            - 'euler forward'
            - 'euler backward'
        (default = 'euler forward')

    Parameters:
        name: str
            Block name.

        initial_state: float | array-like (n,) | array (n,1) (optional)
            Initial value of the integrated state x[0]. (default = zeros)
            If None:
                - If input is known at initialization → x[0] = zeros of the same dimension
                - Otherwise dimension is inferred at the first step

        method: str (optional)
            Integration method. (default = 'euler forward')
            Supported:
                - 'euler forward'
                - 'euler backward'

        sample_time: float | None (optional)
            Block sample time (default = None)

    Inputs:
        in: array (n,1)
            Signal to integrate.

    Outputs:
        out: array (n,1)
            Current integrated state x[k].
    """

    def __init__(self,
        name: str,
        initial_state=None,
        method: str = "euler forward",
        sample_time:float|None = None
    ):
        super().__init__(name, sample_time)
        self.initial_state = initial_state

        # --------------------------- validate method
        self.method = method.lower()
        if self.method not in ("euler forward", "euler backward"):
            raise ValueError(
                f"[{self.name}] Unsupported method '{method}'. "
                f"Allowed: 'euler forward', 'euler backward'."
            )

        if self.method == "euler forward":
            self.direct_feedthrough = False

        # --------------------------- ports
        self.inputs["in"] = None
        self.outputs["out"] = None

        # --------------------------- state
        if initial_state is not None:
            arr = np.asarray(initial_state)
            if arr.ndim == 0:
                arr = arr.reshape(1, 1)
            elif arr.ndim == 1:
                arr = arr.reshape(-1, 1)
            elif arr.ndim == 2 and arr.shape[1] == 1:
                pass
            else:
                raise ValueError(
                    f"[{self.name}] initial_state must be scalar or column vector (n,1). "
                    f"Got shape {arr.shape}."
                )
            self.state["x"] = arr.copy()
        else:
            self.state["x"] = None

        self.next_state["x"] = None


    # ------------------------------------------------------------------
    def initialize(self, t0):
        # Do NOT determine dimension here.
        # Just prepare the structure.
        if self.initial_state is not None:
            x0 = np.asarray(self.initial_state).reshape(-1, 1)
            self.state["x"] = x0
            self.next_state["x"] = x0.copy()
            self.outputs["out"] = x0
        else:
            # Lazy initialization:
            self.state["x"] = None
            self.next_state["x"] = None
            self.outputs["out"] = None  # will be set when first state is created


    # ------------------------------------------------------------------
    def output_update(self, t: float, dt: float):
        x = self.state["x"]

        if x is None:
            # No state yet: output zero vector matching input dimension once known
            u = self.inputs["in"]
            if u is None:
                raise RuntimeError(f"[{self.name}] Input not set during lazy output.")
            u = np.asarray(u).reshape(-1, 1)
            y = np.zeros_like(u)
            self.outputs["out"] = y
            return

        if self.method == "euler forward":
            self.outputs["out"] = x

        elif self.method == "euler backward":
            u = self.inputs["in"]
            if u is None:
                raise RuntimeError(f"[{self.name}] Missing input for backward Euler.")
            u = np.asarray(u).reshape(-1, 1)
            self.outputs["out"] = x + dt * u




    # ------------------------------------------------------------------
    def state_update(self, t, dt):

        u = self.inputs["in"]
        if u is None:
            raise RuntimeError(f"[{self.name}] Input not set during state_update.")

        u = np.asarray(u).reshape(-1, 1)

        # Lazy initialization of state
        if self.state["x"] is None:
            x0 = np.zeros_like(u)
            self.state["x"] = x0
            self.next_state["x"] = x0.copy()

        x = self.state["x"]

        # Compute next state
        x_next = x + dt * u
        self.next_state["x"] = x_next
