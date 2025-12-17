import numpy as np
from pySimBlocks.core.block_source import BlockSource


class Step(BlockSource):
    """
    Step signal source block.

    Summary:
        Generates a step signal that switches from an initial value to a final
        value at a specified time.

    Parameters (overview):
        value_before : float or array-like
            Output value before the step time.
        value_after : float or array-like
            Output value after the step time.
        start_time : float
            Time at which the step occurs.
        sample_time : float, optional
            Block execution period.

    I/O:
        Inputs:
            (none)
        Outputs:
            out : step output signal.

    Notes:
        - The block has no internal state.
        - Scalar parameters are broadcast to all output dimensions.
        - A small tolerance is used to ensure consistent behavior on discrete
          time grids.
    """


    def __init__(self, name: str, value_before, value_after, start_time, sample_time:float|None = None):

        super().__init__(name, sample_time)

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
    def output_update(self, t: float, dt: float):
        self.outputs["out"] = (
            np.copy(self.value_before)
            if t < self.start_time - self.EPS
            else np.copy(self.value_after)
        )
