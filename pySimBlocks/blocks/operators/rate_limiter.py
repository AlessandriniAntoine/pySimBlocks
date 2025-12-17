import numpy as np
from pySimBlocks.core.block import Block


class RateLimiter(Block):
    """
    Discrete-time rate limiter block.

    Summary:
        Limits the rate of change of the output signal by constraining the
        maximum allowed increase and decrease per time step.

    Parameters (overview):
        rising_slope : scalar or vector, optional
            Maximum allowed positive rate of change.
        falling_slope : scalar or vector, optional
            Maximum allowed negative rate of change.
        initial_output : scalar or vector, optional
            Initial output value at the previous time step.
        sample_time : float, optional
            Block execution period.

    I/O:
        Inputs:
            in : Input signal.
        Outputs:
            out : Rate-limited output signal.

    Notes:
        - Stateful block.
        - Direct feedthrough.
        - Rate limits are applied symmetrically per component.
        - Scalar parameters are broadcast to match input dimension.
    """


    direct_feedthrough = True

    # ------------------------------------------------------------------
    def __init__(self,
                 name: str,
                 rising_slope=np.inf,
                 falling_slope=-np.inf,
                 initial_output=None,
                 sample_time:float|None = None):

        super().__init__(name, sample_time)

        self.inputs["in"] = None
        self.outputs["out"] = None

        self.rising_slope = self._to_column("rising_slope", rising_slope)
        self.falling_slope = self._to_column("falling_slope", falling_slope)

        if np.any(self.rising_slope < 0):
            raise ValueError(f"[{self.name}] rising_slope must be >= 0.")
        if np.any(self.falling_slope > 0):
            raise ValueError(f"[{self.name}] falling_slope must be <= 0.")

        self.initial_output = None
        if initial_output is not None:
            self.initial_output = self._to_column("initial_output", initial_output)

        self.state["y"] = None
        self.next_state["y"] = None

    # ------------------------------------------------------------------
    def _to_column(self, name, value):
        arr = np.asarray(value)

        if arr.ndim == 0:
            return arr.reshape(1, 1)
        elif arr.ndim == 1:
            return arr.reshape(-1, 1)
        elif arr.ndim == 2 and arr.shape[1] == 1:
            return arr
        else:
            raise ValueError(
                f"[{self.name}] {name} must be scalar or column vector (n,1), "
                f"got shape {arr.shape}."
            )

    def _broadcast(self, ref, target):
        if target.shape[0] == 1 and ref.shape[0] > 1:
            return np.full_like(ref, target.item())
        return target

    # ------------------------------------------------------------------
    def initialize(self, t0: float):
        u = self.inputs["in"]
        if u is None:
            raise RuntimeError(f"[{self.name}] Input 'in' is None at initialization.")

        u = self._to_column("input", u)

        self.rising_slope = self._broadcast(u, self.rising_slope)
        self.falling_slope = self._broadcast(u, self.falling_slope)

        if self.initial_output is not None:
            y0 = self._broadcast(u, self.initial_output)
        else:
            y0 = u.copy()

        self.state["y"] = y0
        self.outputs["out"] = y0

    # ------------------------------------------------------------------
    def output_update(self, t: float, dt: float):
        u = self.inputs["in"]
        if u is None:
            raise RuntimeError(f"[{self.name}] Input 'in' is None.")

        u = self._to_column("input", u)
        y_prev = self.state["y"]

        du = u - y_prev
        du_min = self.falling_slope * dt
        du_max = self.rising_slope * dt

        du_limited = np.clip(du, du_min, du_max)
        self.outputs["out"] = y_prev + du_limited

    # ------------------------------------------------------------------
    def state_update(self, t: float, dt: float):
        self.next_state["y"] = self.outputs["out"]
