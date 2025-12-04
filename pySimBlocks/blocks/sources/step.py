import numpy as np
from pySimBlocks.core.block import Block


class Step(Block):
    """
    Step signal source.

    Description:
        Computes:
            out(t) = value_before    if t < t_step
            out(t) = value_after     if t ≥ t_step

    Parameters:
        name: str
            Block name.
        value_before: array (n,1)
            Output value before t_step.
        value_after: array (n,1)
            Output value after t_step.
        t_step: float
            Switching time.

    Inputs:
        (none)

    Outputs:
        out: array (n,1)
            Step output vector.
    """

    def __init__(self, name: str,
                 value_before: np.ndarray,
                 value_after: np.ndarray,
                 t_step: float):

        super().__init__(name)

        # Normalize to (n,1)
        vb = np.asarray(value_before).reshape(-1, 1)
        va = np.asarray(value_after).reshape(-1, 1)

        if vb.shape != va.shape:
            raise ValueError("value_before and value_after must have the same shape.")

        self.value_before = vb
        self.value_after = va
        self.t_step = float(t_step)

        # Single output port
        self.outputs["out"] = None


    def initialize(self, t0: float):
        """
        Set output at initialization time t0.
        """
        if t0 < self.t_step:
            self.outputs["out"] = np.copy(self.value_before)
        else:
            self.outputs["out"] = np.copy(self.value_after)

        # No state to initialize.


    def output_update(self, t: float):
        """
        y[k] = step(t)
        """
        if t < self.t_step:
            self.outputs["out"] = np.copy(self.value_before)
        else:
            self.outputs["out"] = np.copy(self.value_after)


    def state_update(self, t: float, dt: float):
        """
        Step source has no internal state.
        """
        pass
