import numpy as np
from numpy.typing import ArrayLike
from pySimBlocks.core.block_source import BlockSource


class Step(BlockSource):
    """
    Step signal source block.

    Summary:
        Generates a step signal that switches from an initial value to a final
        value at a specified time.

    Parameters (overview):
        value_before : float or array-like
            Output value before the step time. Scalar, vector, or matrix.
        value_after : float or array-like
            Output value after the step time. Scalar, vector, or matrix.
        start_time : float
            Time at which the step occurs.
        sample_time : float, optional
            Block execution period.

    I/O:
        Outputs:
            out : step output signal.

    Notes:
        - The block has no internal state.
        - Signals are normalized to 2D arrays:
            scalar -> (1,1), 1D -> (n,1), 2D -> (m,n).
        - If one value is scalar (1,1) and the other is not, scalar is broadcast
          to match the other shape.
        - EPS compensates floating-point rounding to ensure consistent behavior
          on discrete time grids.
    """

    def __init__(
        self,
        name: str,
        value_before: ArrayLike = 0.0,
        value_after: ArrayLike = 1.0,
        start_time: float = 1.0,
        sample_time: float | None = None,
        eps: float = 1e-12,
    ):
        super().__init__(name, sample_time)

        vb = self._to_2d_array("value_before", value_before, dtype=float)
        va = self._to_2d_array("value_after", value_after, dtype=float)

        vb, va = self._match_shapes_with_scalar_broadcast(vb, va)

        # --- Validate start_time ---
        if not isinstance(start_time, (float, int)):
            raise TypeError(f"[{self.name}] start_time must be a float or int.")
        self.start_time = float(start_time)

        self.value_before = vb
        self.value_after = va

        self.outputs["out"] = None
        self.EPS = float(eps)

    # ------------------------------------------------------------------
    @staticmethod
    def _is_scalar_2d(arr: np.ndarray) -> bool:
        return arr.shape == (1, 1)

    def _match_shapes_with_scalar_broadcast(
        self,
        a: np.ndarray,
        b: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        If shapes differ:
          - allow scalar (1,1) to broadcast to the other's shape
          - otherwise raise ValueError
        """
        if a.shape == b.shape:
            return a, b

        a_is_scalar = self._is_scalar_2d(a)
        b_is_scalar = self._is_scalar_2d(b)

        if a_is_scalar and not b_is_scalar:
            return np.full(b.shape, float(a[0, 0])), b

        if b_is_scalar and not a_is_scalar:
            return a, np.full(a.shape, float(b[0, 0]))

        raise ValueError(
            f"[{self.name}] 'value_before' and 'value_after' must have compatible shapes. "
            f"Got {a.shape} vs {b.shape}. Only scalar-to-shape broadcasting is allowed."
        )

    # ------------------------------------------------------------------
    def initialize(self, t0: float) -> None:
        self.outputs["out"] = (
            self.value_before.copy()
            if t0 < self.start_time - self.EPS
            else self.value_after.copy()
        )

    # ------------------------------------------------------------------
    def output_update(self, t: float, dt: float) -> None:
        self.outputs["out"] = (
            self.value_before.copy()
            if t < self.start_time - self.EPS
            else self.value_after.copy()
        )
