import numpy as np
from numpy.typing import ArrayLike
from pySimBlocks.core.block import Block


class DiscreteIntegrator(Block):
    """
    Discrete-time integrator block.

    Summary:
        Integrates an input signal over time using a discrete-time numerical
        integration scheme.

    Parameters:
        initial_state : scalar or array-like, optional
            Initial value of the integrated state. If provided, it FIXES the signal shape.
        method : str
            Numerical integration method: "euler forward" or "euler backward".
        sample_time : float, optional
            Block execution period.

    Inputs:
        in : array (m,n)
            Signal to integrate (must be 2D).

    Outputs:
        out : array (m,n)
            Integrated signal.

    Notes:
        - Stateful block.
        - Direct feedthrough depends on method:
            * euler forward  -> False
            * euler backward -> True
        - Shape is frozen as soon as known (initial_state or first input).
        - No implicit vector reshape; matrices are supported.
    """

    def __init__(
        self,
        name: str,
        initial_state: ArrayLike | None = None,
        method: str = "euler forward",
        sample_time: float | None = None,
    ):
        super().__init__(name, sample_time)

        self.method = method.lower()
        if self.method not in ("euler forward", "euler backward"):
            raise ValueError(
                f"[{self.name}] Unsupported method '{method}'. "
                f"Allowed: 'euler forward', 'euler backward'."
            )

        # direct feedthrough policy
        self.direct_feedthrough = (self.method == "euler backward")

        # ports
        self.inputs["in"] = None
        self.outputs["out"] = None

        # shape policy
        self._resolved_shape: tuple[int, int] | None = None

        # state
        self.state["x"] = None
        self.next_state["x"] = None

        self._initial_state_raw = None
        if initial_state is not None:
            x0 = self._to_2d_array("initial_state", initial_state)
            self._initial_state_raw = x0.copy()
            self._resolved_shape = x0.shape
            self.state["x"] = x0.copy()
            self.next_state["x"] = x0.copy()
            self.outputs["out"] = x0.copy()

    # ------------------------------------------------------------------
    def _ensure_shape(self, u: np.ndarray) -> None:
        if u.ndim != 2:
            raise ValueError(
                f"[{self.name}] Input 'in' must be a 2D array. Got ndim={u.ndim} with shape {u.shape}."
            )

        if self._resolved_shape is None:
            self._resolved_shape = u.shape
            return

        if u.shape != self._resolved_shape:
            raise ValueError(
                f"[{self.name}] Input 'in' shape changed: expected {self._resolved_shape}, got {u.shape}."
            )

    # ------------------------------------------------------------------
    def initialize(self, t0: float) -> None:
        """
        Initialization:
            - If initial_state exists: keep it.
            - Else: keep x=None (lazy). Output stays None until first input appears,
              but output_update will output zeros_like(u) as soon as u exists.
        """
        if self._initial_state_raw is not None:
            x0 = self._initial_state_raw.copy()
            self.state["x"] = x0.copy()
            self.next_state["x"] = x0.copy()
            self.outputs["out"] = x0.copy()
        else:
            self.state["x"] = None
            self.next_state["x"] = None
            self.outputs["out"] = None

    # ------------------------------------------------------------------
    def output_update(self, t: float, dt: float) -> None:
        x = self.state["x"]

        # Lazy case: no state yet -> output based on first available input
        if x is None:
            u = self.inputs["in"]
            if u is None:
                raise RuntimeError(f"[{self.name}] Input 'in' not set during lazy output.")
            u = np.asarray(u, dtype=float)
            self._ensure_shape(u)

            if self.method == "euler forward":
                # y = x, with x(0)=0 for lazy init
                self.outputs["out"] = np.zeros_like(u)
            else:
                # backward: y = x + dt*u, with x(0)=0 for lazy init
                self.outputs["out"] = dt * u
            return

        # State exists -> shape fixed; output depends on method
        if self.method == "euler forward":
            self.outputs["out"] = x.copy()
            return

        # euler backward
        u = self.inputs["in"]
        if u is None:
            raise RuntimeError(f"[{self.name}] Missing input for backward Euler.")
        u = np.asarray(u, dtype=float)
        self._ensure_shape(u)
        if u.shape != x.shape:
            raise ValueError(f"[{self.name}] Input shape {u.shape} incompatible with state shape {x.shape}.")
        self.outputs["out"] = x + dt * u

    # ------------------------------------------------------------------
    def state_update(self, t: float, dt: float) -> None:
        u = self.inputs["in"]
        if u is None:
            raise RuntimeError(f"[{self.name}] Input 'in' not set during state_update.")

        u = np.asarray(u, dtype=float)
        self._ensure_shape(u)

        # Lazy initialization of state at first state_update
        if self.state["x"] is None:
            x = np.zeros_like(u)
            self.state["x"] = x.copy()
        else:
            x = self.state["x"]

        if x.shape != u.shape:
            raise ValueError(f"[{self.name}] Input shape {u.shape} incompatible with state shape {x.shape}.")

        self.next_state["x"] = x + dt * u
