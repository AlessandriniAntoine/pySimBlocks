import numpy as np
from pySimBlocks.core.block import Block


class ZeroOrderHold(Block):
    """
    Zero-Order Hold (ZOH) block.

    Description:
        Samples the input signal at discrete instants and holds its value
        constant between sampling instants.

        Discrete semantics (mono-rate V1):
            y[k] = u[k_sample]   with k_sample = last sampling instant

        This block models signal sampling semantics only.
        It does NOT control execution rate.

    Parameters:
        name: str
            Block name.

        sample_time: float
            Sampling period Ts > 0.

    Inputs:
        in: array (n,1)
            Input signal.

    Outputs:
        out: array (n,1)
            Held output signal.
    """

    direct_feedthrough = True

    # ------------------------------------------------------------------
    def __init__(self,
                 name: str,
                 sample_time: float):

        super().__init__(name, sample_time)

        self.inputs["in"] = None
        self.outputs["out"] = None

        self.state["y"] = None
        self.next_state["y"] = None
        self.state["t_last"] = None
        self.next_state["t_last"] = None

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

    # ------------------------------------------------------------------
    def initialize(self, t0: float):
        u = self.inputs["in"]
        if u is None:
            raise RuntimeError(f"[{self.name}] Input 'in' is None at initialization.")

        u = self._to_column("input", u)
        y0 = u.copy()

        self.state["y"] = y0
        self.state["t_last"] = t0

        self.outputs["out"] = y0

    # ------------------------------------------------------------------
    def output_update(self, t: float, dt: float):
        u = self.inputs["in"]
        if u is None:
            raise RuntimeError(f"[{self.name}] Input 'in' is None.")

        u = self._to_column("input", u)

        t_last = self.state["t_last"]

        if (t - t_last) >= self.sample_time - 1e-12:
            self.outputs["out"] = u
        else:
            self.outputs["out"] = self.state["y"]

    # ------------------------------------------------------------------
    def state_update(self, t: float, dt: float):
        t_last = self.state["t_last"]

        if (t - t_last) >= self.sample_time - 1e-12:
            self.next_state["y"] = self.outputs["out"]
            self.next_state["t_last"] = t
        else:
            self.next_state["y"] = self.state["y"]
            self.next_state["t_last"] = self.state["t_last"]
