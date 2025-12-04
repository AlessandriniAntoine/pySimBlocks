import numpy as np
from pySimBlocks.core.block import Block


class Delay(Block):
    """
    N-step discrete delay.

    Description:
        Implements:
            out[k] = in[k - N]
        using an internal shift buffer of length N.

    Parameters:
        name: str
            Block name.
        num_delays: int
            Number of discrete delays N ≥ 1.
        initial_output: array (n,1) (optional)
            Initial buffer fill value.

    Inputs:
        in: array (n,1)
            Current input signal in[k].

    Outputs:
        out: array (n,1)
            Delayed signal in[k - N].
    """

    def __init__(self, name: str, num_delays: int = 1,
                 initial_output: np.ndarray | None = None):

        super().__init__(name)

        if num_delays < 1:
            raise ValueError("num_delays must be >= 1.")

        self.num_delays = int(num_delays)

        # Ports
        self.inputs["in"] = None        # u[k]
        self.outputs["out"] = None      # y[k] = u[k - N]

        # Internal state = buffer of length N
        if initial_output is not None:
            init = np.asarray(initial_output).reshape(-1, 1)
            self.state["buffer"] = [init.copy() for _ in range(self.num_delays)]
        else:
            # Initialized later when dimension is known
            self.state["buffer"] = None

        # next_state will contain the updated buffer after each step
        self.next_state["buffer"] = None

    # ------------------------------------------------------------------
    # INITIALIZATION
    # ------------------------------------------------------------------
    def initialize(self, t0: float):
        """
        Initialize buffer based on initial_output or zeros.
        Also compute initial output y[0].
        """
        buffer = self.state["buffer"]
        u = self.inputs["in"]

        # Case 1: user provided initial_output
        if buffer is not None:
            self.outputs["out"] = buffer[0].copy()
            return

        # Case 2: No initial_output provided → auto-init
        # If u is already known at initialization:
        if u is not None:
            u = np.asarray(u).reshape(-1, 1)
            self.state["buffer"] = [u.copy() for _ in range(self.num_delays)]
            self.outputs["out"] = u.copy()
            return

        # Case 3: u unknown → initialize to zeros
        # Dimension is unknown until input arrives → leave None, output None.
        self.state["buffer"] = None
        self.outputs["out"] = None

    # ------------------------------------------------------------------
    # PHASE 1 : OUTPUT UPDATE
    # ------------------------------------------------------------------
    def output_update(self, t: float):
        """
        y[k] = buffer[0]
        """
        buffer = self.state["buffer"]

        if buffer is None:
            raise RuntimeError(f"[{self.name}] Delay buffer uninitialized.")

        self.outputs["out"] = buffer[0].copy()

    # ------------------------------------------------------------------
    # PHASE 2 : STATE UPDATE
    # ------------------------------------------------------------------
    def state_update(self, t: float, dt: float):
        """
        buffer[k+1] = shift_left(buffer[k]) + u[k] at the end.
        """
        u = self.inputs["in"]
        if u is None:
            raise RuntimeError(f"[{self.name}] Input 'in' is not connected or not set.")

        u = np.asarray(u).reshape(-1, 1)

        buffer = self.state["buffer"]

        # If buffer was None (unknown size), initialize now
        if buffer is None:
            zeros = np.zeros_like(u)
            buffer = [zeros.copy() for _ in range(self.num_delays)]

        # Shift buffer left
        new_buffer = []
        for i in range(self.num_delays - 1):
            new_buffer.append(buffer[i + 1].copy())

        # Append newest input u[k]
        new_buffer.append(u.copy())

        self.next_state["buffer"] = new_buffer
