import numpy as np
from pySimBlocks.core.block import Block


class Saturation(Block):
    """
    Discrete-time saturation operator.

    Summary:
        Applies element-wise saturation to the input signal by enforcing
        lower and upper bounds.

    Parameters (overview):
        u_min : scalar or vector, optional
            Lower saturation bound.
        u_max : scalar or vector, optional
            Upper saturation bound.
        sample_time : float, optional
            Block execution period.

    I/O:
        Inputs:
            in : Input signal.
        Outputs:
            out : Saturated output signal.

    Notes:
        - Stateless block.
        - Direct feedthrough.
        - Bounds are applied component-wise.
        - Scalar bounds are broadcast to match input dimension.
    """


    direct_feedthrough = True

    # ------------------------------------------------------------------
    def __init__(self, name: str, u_min=-np.inf, u_max=np.inf, sample_time:float|None = None):
        super().__init__(name, sample_time)

        self.inputs["in"] = None
        self.outputs["out"] = None

        self.u_min = self._to_column("u_min", u_min)
        self.u_max = self._to_column("u_max", u_max)

        if np.any(self.u_min > self.u_max):
            raise ValueError(
                f"[{self.name}] u_min must be <= u_max for all components."
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
        self.u_min = self._broadcast(u, self.u_min)
        self.u_max = self._broadcast(u, self.u_max)

        self.outputs["out"] = np.clip(u, self.u_min, self.u_max)

    # ------------------------------------------------------------------
    def output_update(self, t: float, dt: float):
        u = self.inputs["in"]
        if u is None:
            raise RuntimeError(f"[{self.name}] Input 'in' is None.")

        u = self._to_column("input", u)
        self.outputs["out"] = np.clip(u, self.u_min, self.u_max)

    # ------------------------------------------------------------------
    def state_update(self, t: float, dt: float):
        # Stateless block
        pass
