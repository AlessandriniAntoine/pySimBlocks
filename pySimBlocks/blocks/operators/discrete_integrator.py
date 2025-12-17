import numpy as np
from pySimBlocks.core.block import Block


class DiscreteIntegrator(Block):
    """
    Discrete-time integrator block.

    Summary:
        Integrates an input signal over time using a discrete-time numerical
        integration scheme.

    Parameters (overview):
        initial_state : scalar or vector, optional
            Initial value of the integrated state.
        method : str
            Numerical integration method.
        sample_time : float, optional
            Block execution period.

    I/O:
        Inputs:
            in : Signal to integrate.
        Outputs:
            out : Integrated signal.

    Notes:
        - Stateful block.
        - Direct feedthrough depends on the integration method.
        - Uses forward or backward Euler integration.
        - State dimension is inferred lazily from the first input if not
          explicitly initialized.
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
