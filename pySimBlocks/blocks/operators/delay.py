import numpy as np
from pySimBlocks.core.block import Block


class Delay(Block):
    """
    N-step discrete delay block.

    Summary:
        Outputs a delayed version of the input signal by a fixed number of
        discrete time steps.

    Parameters (overview):
        num_delays : int
            Number of discrete delays N (N ≥ 1).
        initial_output : scalar or vector, optional
            Initial value used to fill the delay buffer.
        sample_time : float, optional
            Block execution period.

    I/O:
        Inputs:
            in : Input signal.
        Outputs:
            out : Delayed output signal.

    Notes:
        - Stateful block.
        - No direct feedthrough.
        - Output at time k is the input at time k − N.
        - Buffer dimension is inferred from the first available input if not
          explicitly initialized.
    """


    direct_feedthrough = False

    def __init__(self,
            name: str,
            num_delays: int = 1,
            initial_output=None,
            sample_time:float|None = None):
        super().__init__(name, sample_time)

        if not isinstance(num_delays, int) or num_delays < 1:
            raise ValueError(f"[{self.name}] num_delays must be >= 1.")

        self.num_delays = num_delays

        # Ports
        self.inputs["in"] = None
        self.outputs["out"] = None

        # -------------------------------
        # Validate initial_output (NEW)
        # -------------------------------
        if initial_output is not None:
            arr = np.asarray(initial_output)

            # Accepted shapes : scalar, (n,), (n,1)
            if arr.ndim == 0:
                arr = arr.reshape(1, 1)
            elif arr.ndim == 1:
                arr = arr.reshape(-1, 1)
            elif arr.ndim == 2 and arr.shape[1] == 1:
                pass
            else:
                raise ValueError(
                    f"[{self.name}] initial_output must be scalar or vector (n,1). Got shape {arr.shape}."
                )

            self.state["buffer"] = [arr.copy() for _ in range(self.num_delays)]

        else:
            # Dimension unknown until initialize or state_update
            self.state["buffer"] = None

        self.next_state["buffer"] = None

    # ------------------------------------------------------------------
    def initialize(self, t0: float):
        """
        Initialize buffer using:
        - initial_output if provided
        - input u[0] if known
        - otherwise leave buffer=None
        """
        buffer = self.state["buffer"]
        u = self.inputs["in"]

        # Case 1: user provided initial_output
        if buffer is not None:
            self.outputs["out"] = buffer[0].copy()
            return

        # Case 2: u available → infer dimension
        if u is not None:
            u = np.asarray(u)
            if u.ndim != 2 or u.shape[1] != 1:
                raise ValueError(
                    f"[{self.name}] Input 'in' must be a column vector (n,1). Got {u.shape}."
                )

            u = u.reshape(-1, 1)
            self.state["buffer"] = [u.copy() for _ in range(self.num_delays)]
            self.outputs["out"] = u.copy()
            return

        # Case 3: dimension unknown → defer
        self.outputs["out"] = None

    # ------------------------------------------------------------------
    def output_update(self, t: float, dt: float):
        buffer = self.state["buffer"]

        # NEW: If buffer not initialized, infer dimension from current input
        if buffer is None:
            u = self.inputs["in"]
            if u is None:
                raise RuntimeError(f"[{self.name}] Delay buffer uninitialized (no input).")

            u = np.asarray(u)
            if u.ndim != 2 or u.shape[1] != 1:
                raise ValueError(
                    f"[{self.name}] Input 'in' must be a column vector (n,1). Got {u.shape}."
                )

            u = u.reshape(-1, 1)

            # Initialize buffer with zeros *of correct dimension*
            zeros = np.zeros_like(u)
            self.state["buffer"] = [zeros.copy() for _ in range(self.num_delays)]
            buffer = self.state["buffer"]

        # Now buffer is guaranteed to exist
        self.outputs["out"] = buffer[0].copy()

    # ------------------------------------------------------------------
    def state_update(self, t: float, dt: float):
        u = self.inputs["in"]
        if u is None:
            raise RuntimeError(f"[{self.name}] Input 'in' is not connected or not set.")

        u = np.asarray(u)
        if u.ndim != 2 or u.shape[1] != 1:
            raise ValueError(
                f"[{self.name}] Input 'in' must be a column vector (n,1). Got {u.shape}."
            )

        u = u.reshape(-1, 1)
        buffer = self.state["buffer"]

        # Case: dimension still unknown → initialize buffer of zeros
        if buffer is None:
            zeros = np.zeros_like(u)
            buffer = [zeros.copy() for _ in range(self.num_delays)]

        # Shift buffer left and append u
        new_buffer = []
        for i in range(self.num_delays - 1):
            new_buffer.append(buffer[i + 1].copy())

        new_buffer.append(u.copy())

        self.next_state["buffer"] = new_buffer
