import numpy as np
from pySimBlocks.core.block import Block

class BlockSource(Block):
    """
    Base class for all source blocks (Constant, Step, Ramp, Sinusoidal, ...).

    Provides:
        - vector normalization utilities
        - no state update by default
    """


    direct_feedthrough = False
    is_source = True

    def __init__(self, name: str, sample_time: float | None=None):
        super().__init__(name, sample_time)

    # Utility used by all sources
    def _to_column_vector(self, param_name, value):
        arr = np.asarray(value)

        if arr.ndim == 0:
            return arr.reshape(1, 1)
        elif arr.ndim == 1:
            return arr.reshape(-1, 1)
        elif arr.ndim == 2:
            if arr.shape[0] == 1:
                return arr.reshape(-1, 1)
            elif arr.shape[1] == 1:
                return arr
            else:
                raise ValueError(
                    f"[{self.name}] '{param_name}' must be scalar or vector, got {arr.shape}."
                )
        else:
            raise ValueError(
                f"[{self.name}] '{param_name}' has too many dimensions: ndim={arr.ndim}"
            )

    def state_update(self, t, dt):
        pass  # all sources are stateless
