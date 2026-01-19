import numpy as np
from numpy.typing import ArrayLike
from pySimBlocks.core.block_source import BlockSource


class Constant(BlockSource):
    """
    Constant signal source block.

    Summary:
        Generates a constant output signal with a fixed value over time.
        The output does not depend on time or any input signal.

    Parameters (overview):
        value : float or array-like
            Constant output value. Can be scalar, vector, or matrix.
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
        - Scalar values are normalized to shape (1,1).
        - 1D values are normalized to column vectors (n,1).
        - 2D values are preserved as matrices (m,n).
    """

    def __init__(
        self,
        name: str,
        value: ArrayLike = 1.0,
        sample_time: float | None = None,
    ):
        super().__init__(name, sample_time)

        # Accept numeric scalars and array-like
        if not isinstance(value, (list, tuple, np.ndarray, float, int)):
            raise TypeError(
                f"[{self.name}] Constant 'value' must be numeric or array-like."
            )

        arr = self._to_2d_array("value", value, dtype=float)

        self.value = arr
        self.outputs["out"] = arr.copy()

    # ------------------------------------------------------------------
    def initialize(self, t0: float) -> None:
        self.outputs["out"] = self.value.copy()

    # ------------------------------------------------------------------
    def output_update(self, t: float, dt: float) -> None:
        self.outputs["out"] = self.value.copy()
