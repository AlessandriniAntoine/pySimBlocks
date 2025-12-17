import numpy as np
from pySimBlocks.core.block import Block


class DeadZone(Block):
    """
    Discrete-time dead zone operator.

    Summary:
        Suppresses the input signal within a specified interval around zero
        and shifts the signal outside this interval.

    Parameters (overview):
        lower_bound : scalar or vector
            Lower bound of the dead zone (must be <= 0).
        upper_bound : scalar or vector
            Upper bound of the dead zone (must be >= 0).
        sample_time : float, optional
            Block execution period.

    I/O:
        Inputs:
            in : Input signal.
        Outputs:
            out : Output signal after dead-zone transformation.

    Notes:
        - Stateless block.
        - Direct feedthrough.
        - Bounds are broadcast to match input dimension.
        - The dead zone must include zero.
    """


    direct_feedthrough = True

    # ------------------------------------------------------------------
    def __init__(self,
                 name: str,
                 lower_bound=0.0,
                 upper_bound=0.0,
                 sample_time:float|None = None):

        super().__init__(name, sample_time)

        self.inputs["in"] = None
        self.outputs["out"] = None

        self.lower_bound = self._to_column("lower_bound", lower_bound)
        self.upper_bound = self._to_column("upper_bound", upper_bound)

        if np.any(self.lower_bound > self.upper_bound):
            raise ValueError(
                f"[{self.name}] lower_bound must be <= upper_bound."
            )
        if np.any(self.lower_bound > 0):
            raise ValueError(
                f"[{self.name}] lower_bound must be <= 0."
            )
        if np.any(self.upper_bound < 0):
            raise ValueError(
                f"[{self.name}] upper_bound must be >= 0."
            )

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

    def _broadcast(self, ref, bound):
        if bound.shape[0] == 1 and ref.shape[0] > 1:
            return np.full_like(ref, bound.item())
        return bound

    # ------------------------------------------------------------------
    def initialize(self, t0: float):
        u = self.inputs["in"]
        if u is None:
            raise RuntimeError(f"[{self.name}] Input 'in' is None at initialization.")

        u = self._to_column("input", u)

        self.lower_bound = self._broadcast(u, self.lower_bound)
        self.upper_bound = self._broadcast(u, self.upper_bound)

        self.outputs["out"] = self._apply_dead_zone(u)

    # ------------------------------------------------------------------
    def output_update(self, t: float, dt: float):
        u = self.inputs["in"]
        if u is None:
            raise RuntimeError(f"[{self.name}] Input 'in' is None.")

        u = self._to_column("input", u)
        self.outputs["out"] = self._apply_dead_zone(u)

    # ------------------------------------------------------------------
    def state_update(self, t: float, dt: float):
        # Stateless block
        pass

    # ------------------------------------------------------------------
    def _apply_dead_zone(self, u):
        y = np.zeros_like(u)

        above = u > self.upper_bound
        below = u < self.lower_bound

        y[above] = u[above] - self.upper_bound[above]
        y[below] = u[below] - self.lower_bound[below]

        return y
