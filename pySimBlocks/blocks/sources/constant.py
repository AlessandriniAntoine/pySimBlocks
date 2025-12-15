import numpy as np
from pySimBlocks.core.block_source import BlockSource


class Constant(BlockSource):

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

    def __init__(self, name: str, value, sample_time:float|None = None):
        super().__init__(name, sample_time)

        if not isinstance(value, (list, tuple, np.ndarray, float, int)):
            raise TypeError(f"[{self.name}] Constant 'value' must be numeric or array-like.")

        arr = np.asarray(value)
        arr = self._to_column_vector("value", arr)

        # Correct final assignment
        self.value = arr
        self.outputs["out"] = np.copy(arr)

    # ------------------------------------------------------------------
    def initialize(self, t0: float) -> None:
        self.outputs["out"] = np.copy(self.value)

    # ------------------------------------------------------------------
    def output_update(self, t: float, dt: float) -> None:
        self.outputs["out"] = np.copy(self.value)
