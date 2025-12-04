import numpy as np
from pySimBlocks.core.block import Block


class Constant(Block):

    """
    Constant signal source.

    Description:
        Computes:
            out(t) = value

    Parameters:
        name: str
            Block name.
        value: array (n,1)
            Constant output value.

    Inputs:
        (none)

    Outputs:
        out: array (n,1)
            Constant output vector.
    """


    def __init__(
        self,
        name: str,
        value: np.ndarray,
    ):
        super().__init__(name)

        value = np.asarray(value).reshape(-1, 1)

        self.value = value
        self.outputs["out"] = np.copy(self.value)


    def initialize(self, t0: float) -> None:
        self.outputs["out"] = np.copy(self.value)


    def output_update(self, t: float) -> None:
        self.outputs["out"] = np.copy(self.value)


    def state_update(self, t: float, dt: float) -> None:
        pass
