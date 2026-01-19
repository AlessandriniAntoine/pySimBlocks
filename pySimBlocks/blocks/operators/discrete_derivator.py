import numpy as np
from numpy.typing import ArrayLike
from pySimBlocks.core.block import Block


class DiscreteDerivator(Block):
    """
    Discrete-time differentiator block.

    Summary:
        Estimates the discrete-time derivative of the input signal using a
        backward finite difference:
            y[k] = (u[k] - u[k-1]) / dt

    Parameters:
        initial_output : scalar or array-like, optional
            Output used at the first execution step.
            If provided, it also FIXES the signal shape permanently.
        sample_time : float, optional
            Block execution period.

    Inputs:
        in : array (m,n)
            Input signal (must be 2D).

    Outputs:
        out : array (m,n)
            Estimated discrete-time derivative.

    Notes:
        - Stateful block.
        - Direct feedthrough.
        - Shape is frozen as soon as known (initial_output or first input).
        - No implicit vector reshape; matrices are supported.
    """

    direct_feedthrough = True

    def __init__(
        self,
        name: str,
        initial_output: ArrayLike | None = None,
        sample_time: float | None = None,
    ):
        super().__init__(name, sample_time)

        self.inputs["in"] = None
        self.outputs["out"] = None

        self.state["u_prev"] = None
        self.next_state["u_prev"] = None

        self._resolved_shape: tuple[int, int] | None = None
        self._first_output = True

        self._initial_output_raw = None
        if initial_output is not None:
            y0 = self._to_2d_array("initial_output", initial_output)
            # initial_output fixes the shape (even (1,1))
            self._initial_output_raw = y0.copy()
            self.outputs["out"] = y0.copy()
            self._resolved_shape = y0.shape

    # -------------------------------------------------------
    def _ensure_shape(self, u: np.ndarray) -> None:
        if u.ndim != 2:
            raise ValueError(
                f"[{self.name}] Input 'in' must be a 2D array. Got ndim={u.ndim} with shape {u.shape}."
            )

        if self._resolved_shape is None:
            self._resolved_shape = u.shape
            # If no initial_output was provided, initialize output to zeros now
            if self.outputs["out"] is None:
                self.outputs["out"] = np.zeros_like(u)
            return

        if u.shape != self._resolved_shape:
            raise ValueError(
                f"[{self.name}] Input 'in' shape changed: expected {self._resolved_shape}, got {u.shape}."
            )

    # -------------------------------------------------------
    def initialize(self, t0: float) -> None:
        """
        Initialization rules:
            - If initial_output exists: keep it as current output.
            - If input exists: freeze shape (if not already), and set u_prev = u(0).
            - If input missing: do not create u_prev; output remains
              (initial_output if provided, else None).
        """
        u = self.inputs["in"]
        if u is None:
            # If initial_output exists, it's already set and shape fixed.
            # Else output stays None until first input appears.
            self.state["u_prev"] = None
            self.next_state["u_prev"] = None
            return

        u = np.asarray(u, dtype=float)
        self._ensure_shape(u)

        self.state["u_prev"] = u.copy()
        self.next_state["u_prev"] = u.copy()

        # If no initial_output given, ensure out exists (zeros_like(u))
        if self.outputs["out"] is None:
            self.outputs["out"] = np.zeros_like(u)

    # -------------------------------------------------------
    def output_update(self, t: float, dt: float) -> None:
        """
        First call policy:
            - If initial_output was provided: keep it for the first output_update call.
            - Otherwise: output zeros on the first call.

        Afterwards:
            y = (u - u_prev) / dt
        """
        u = self.inputs["in"]
        if u is None:
            raise RuntimeError(f"[{self.name}] Input 'in' not set.")

        u = np.asarray(u, dtype=float)
        self._ensure_shape(u)

        if self._first_output:
            self._first_output = False
            # Keep initial_output if it exists, otherwise enforce zeros
            if self.outputs["out"] is None:
                self.outputs["out"] = np.zeros_like(u)
            return

        u_prev = self.state["u_prev"]
        if u_prev is None:
            # No previous value -> derivative defined as zero
            self.outputs["out"] = np.zeros_like(u)
            return

        # shape already enforced by _ensure_shape
        self.outputs["out"] = (u - u_prev) / dt

    # -------------------------------------------------------
    def state_update(self, t: float, dt: float) -> None:
        """
        Update previous input.
        """
        u = self.inputs["in"]
        if u is None:
            raise RuntimeError(f"[{self.name}] Input 'in' not set.")

        u = np.asarray(u, dtype=float)
        self._ensure_shape(u)

        self.next_state["u_prev"] = u.copy()
