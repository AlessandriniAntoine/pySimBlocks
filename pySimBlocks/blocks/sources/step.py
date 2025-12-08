import numpy as np
from pySimBlocks.core.block_source import BlockSource


class Step(BlockSource):
    """
    Step signal source.

    Description:
        Computes:
            out(t) = value_before    if t < start_time
            out(t) = value_after     if t ≥ start_time

    Parameters:
        name: str
            Block name.
        value_before: float | array-like (n,) | array (n,1)
            Output value before start_time.
        value_after: float | array-like (n,) | array (n,1)
            Output value after start_time.
        start_time: float
            Switching time.

    Inputs:
        (none)

    Outputs:
        out: array (n,1)
            Step output vector.
    """

    def __init__(self, name: str, value_before, value_after, start_time):

        super().__init__(name)

        # --- Validate and normalize values ---
        vb = np.asarray(value_before)
        va = np.asarray(value_after)

        # reshape using the same rules as Constant
        vb = self._to_column_vector("value_before", vb)
        va = self._to_column_vector("value_after", va)

        if vb.shape != va.shape:
            raise ValueError(
                f"[{self.name}] 'value_before' and 'value_after' must have same shape. "
                f"Got {vb.shape} vs {va.shape}."
            )

        self.value_before = vb
        self.value_after = va

        # --- Validate start_time ---
        if not isinstance(start_time, (float, int)):
            raise TypeError(f"[{self.name}] start_time must be a float or int.")

        self.start_time = float(start_time)

        # Output port
        self.outputs["out"] = None

        self.EPS = 1e-12 # This compensates for floating-point rounding and restores correct behavior on all time grids.


    # ------------------------------------------------------------------
    def initialize(self, t0: float):
        self.outputs["out"] = (
            np.copy(self.value_before)
            if t0 < self.start_time - self.EPS
            else np.copy(self.value_after)
        )

    # ------------------------------------------------------------------
    def output_update(self, t: float):
        self.outputs["out"] = (
            np.copy(self.value_before)
            if t < self.start_time - self.EPS
            else np.copy(self.value_after)
        )
