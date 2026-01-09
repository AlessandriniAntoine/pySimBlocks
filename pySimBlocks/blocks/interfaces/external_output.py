import numpy as np
from pySimBlocks.core.block import Block


class ExternalOutput(Block):
    """
    External output interface block.

    Summary:
        Pass-through block for external real-time commands/values.

    Parameters:
        sample_time: float, optional
            Execution period of the block. If not specified, the simulator time
            step is used.

    I/O:
        Input:
            in: array (n,1)
                Value produced by the model. Scalar, (n,), (n,1) accepted.
        Output:
            out: array (n,1)
                Value forwarded to the external side as a column vector (n,1).
    """

    def __init__(self, name: str, sample_time: float | None = None):
        super().__init__(name, sample_time)
        self.inputs["in"] = None
        self.outputs["out"] = None

    # ------------------------------------------------------------------
    @staticmethod
    def _to_column(value, *, block_name: str, port_name: str) -> np.ndarray:
        """
        Convert scalar / (n,) / (n,1) to a strict (n,1) ndarray.
        """
        arr = np.asarray(value)

        # scalar
        if arr.ndim == 0:
            return arr.reshape(1, 1)

        # vector (n,)
        if arr.ndim == 1:
            return arr.reshape(-1, 1)

        # column (n,1)
        if arr.ndim == 2 and arr.shape[1] == 1:
            return arr

        raise ValueError(
            f"[{block_name}] Input '{port_name}' must be scalar, (n,), or (n,1). "
            f"Got shape {arr.shape}."
        )

    # ------------------------------------------------------------------
    def initialize(self, t0: float) -> None:
        u = self.inputs["in"]
        if u is None:
            self.outputs["out"] = None
            return

        self.outputs["out"] = self._to_column(u, block_name=self.name, port_name="in")

    # ------------------------------------------------------------------
    def output_update(self, t: float, dt: float) -> None:
        u = self.inputs["in"]
        if u is None:
            raise RuntimeError(f"[{self.name}] Missing input 'in'.")

        self.outputs["out"] = self._to_column(u, block_name=self.name, port_name="in")

    # ------------------------------------------------------------------
    def state_update(self, t: float, dt: float) -> None:
        # Stateless block
        pass
