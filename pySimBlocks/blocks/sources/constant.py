import numpy as np
from pySimBlocks.core.block_source import BlockSource


class Constant(BlockSource):
    """
    Constant signal source block.

    Summary:
        Generates a constant output signal with a fixed value over time.
        The output does not depend on time or any input signal.

    Parameters (overview):
        value : float or array-like
            Constant output value.
        sample_time : float, optional
            Block execution period.

    I/O:
        Inputs:
            (none)
        Outputs:
            out : constant output signal.

    Notes:
        - The block has no internal state.
        - The output value is held constant for the entire simulation.
        - If value is scalar, the output is a (1,1) signal.
        - If value is vector-valued, it is converted to a column vector.
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
