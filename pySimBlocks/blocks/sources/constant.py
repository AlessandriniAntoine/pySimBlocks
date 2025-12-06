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
        value: float | array-like (n,) | array (n,1)
            Constant output value.

    Inputs:
        (none)

    Outputs:
        out: array (n,1)
            Constant output vector.
    """

    def __init__(self, name: str, value):
        super().__init__(name)

        if not isinstance(value, (list, tuple, np.ndarray, float, int)):
            raise TypeError(f"[{self.name}] Constant 'value' must be numeric or array-like.")

        arr = np.asarray(value)

        if arr.ndim == 0:              # scalar
            arr = arr.reshape(1, 1)

        elif arr.ndim == 1:            # vector (n,)
            arr = arr.reshape(-1, 1)

        elif arr.ndim == 2:
            if arr.shape[0] == 1:      # row vector
                arr = arr.reshape(-1, 1)
            elif arr.shape[1] == 1:    # column vector
                pass
            else:
                raise ValueError(
                    f"[{self.name}] Constant 'value' must be scalar or vector. "
                    f"Got matrix of shape {arr.shape}."
                )
        else:
            raise ValueError(f"[{self.name}] Constant 'value' has too many dimensions.")

        # Correct final assignment
        self.value = arr
        self.outputs["out"] = np.copy(arr)

    def initialize(self, t0: float) -> None:
        self.outputs["out"] = np.copy(self.value)

    def output_update(self, t: float) -> None:
        self.outputs["out"] = np.copy(self.value)

    def state_update(self, t: float, dt: float) -> None:
        pass
