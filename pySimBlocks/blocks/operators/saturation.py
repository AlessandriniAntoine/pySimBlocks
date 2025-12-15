import numpy as np
from pySimBlocks.core.block import Block


class Saturation(Block):
    """
    Discrete-time saturation operator.

    Description:
        Applies element-wise saturation to the input signal:

            y[k] = clip(u[k], u_min, u_max)

        Absence of saturation is represented by infinite bounds.

    Parameters:
        name: str
            Block name.

        u_min: float | array-like (n,) | array (n,1) (optional)
            Lower saturation bound. (Default = -inf)

        u_max: float | array-like (n,) | array (n,1) (optional)
            Upper saturation bound. (Default = +inf)

    Inputs:
        in: array (n,1)
            Input signal.

    Outputs:
        out: array (n,1)
            Saturated output signal.
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
