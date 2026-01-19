import numpy as np
from numpy.typing import ArrayLike
from pySimBlocks.core.block import Block


class Delay(Block):
    """
    N-step discrete delay block.

    Summary:
        Outputs a delayed version of the input signal by a fixed number of
        discrete time steps.

    Parameters (overview):
        num_delays : int
            Number of discrete delays N (N >= 1).
        initial_output : scalar or array-like, optional
            Initial value used to fill the delay buffer.
            Accepted: scalar -> (1,1), 1D -> (k,1), 2D -> (m,n).
            Scalar (1,1) can be broadcast to match the input shape when the
            first input becomes available.
        sample_time : float, optional
            Block execution period.

    I/O:
        Inputs:
            in : Input signal (must be 2D).
        Outputs:
            out : Delayed output signal (2D).

    Notes:
        - Stateful block.
        - No direct feedthrough.
        - Output at time k is the input at time k − N.
        - Buffer shape is inferred from the first available input if not
          explicitly initialized.
    """

    direct_feedthrough = False

    def __init__(
        self,
        name: str,
        num_delays: int = 1,
        initial_output: ArrayLike | None = None,
        sample_time: float | None = None,
    ):
        super().__init__(name, sample_time)

        if not isinstance(num_delays, int) or num_delays < 1:
            raise ValueError(f"[{self.name}] num_delays must be >= 1.")
        self.num_delays = num_delays

        self.inputs["in"] = None
        self.outputs["out"] = None

        self.state["buffer"] = None
        self.next_state["buffer"] = None

        self._buffer_shape: tuple[int, int] | None = None
        self._initial_value: np.ndarray | None = None

        if initial_output is not None:
            arr = self._to_2d_array("initial_output", initial_output)
            self._initial_value = arr  # may be scalar (1,1) or non-scalar
            # If non-scalar, we already know the buffer shape now.
            if arr.shape != (1, 1):
                self._buffer_shape = arr.shape
                self.state["buffer"] = [arr.copy() for _ in range(self.num_delays)]

    # ------------------------------------------------------------------
    def _ensure_buffer_initialized(self, u: np.ndarray) -> None:
        """
        Ensure buffer exists and has a fixed, constant shape.

        Policy (strict):
            - u must be 2D
            - once buffer shape is known, it must never change (including (1,1))
            - if buffer not initialized, infer shape from:
                * existing non-scalar initial_output (already initialized in __init__)
                * otherwise from the first available input u
            - if initial_output is scalar (1,1) and first input is non-scalar:
                * broadcast scalar to input shape ONCE at initialization time (allowed only
                  if buffer shape was not previously fixed)
            - after initialization, any input shape mismatch raises ValueError
        """
        if u.ndim != 2:
            raise ValueError(
                f"[{self.name}] Input 'in' must be a 2D array. Got ndim={u.ndim} with shape {u.shape}."
            )

        # If buffer already exists, enforce strict shape match
        if self.state["buffer"] is not None:
            expected = self.state["buffer"][0].shape
            if u.shape != expected:
                raise ValueError(
                    f"[{self.name}] Input 'in' shape changed or mismatched with buffer: "
                    f"expected {expected}, got {u.shape}."
                )
            return

        # Buffer not initialized yet: decide the target shape
        target_shape = None

        # If a non-scalar initial_output was provided, __init__ already initialized buffer,
        # so we should not reach here. Keep for safety.
        if self._buffer_shape is not None:
            target_shape = self._buffer_shape
        else:
            target_shape = u.shape

        # Initialize buffer
        # If initial_output is scalar, broadcast it to target_shape (only at initialization)
        if self._initial_value is not None and self._initial_value.shape == (1, 1):
            scalar = float(self._initial_value[0, 0])
            init = np.full(target_shape, scalar, dtype=float)
            self.state["buffer"] = [init.copy() for _ in range(self.num_delays)]
            self._buffer_shape = target_shape
            return

        # Default: zeros
        zeros = np.zeros(target_shape, dtype=float)
        self.state["buffer"] = [zeros.copy() for _ in range(self.num_delays)]
        self._buffer_shape = target_shape

    # ------------------------------------------------------------------
    def initialize(self, t0: float) -> None:
        buffer = self.state["buffer"]
        u = self.inputs["in"]

        # If buffer already exists (non-scalar initial_output case)
        if buffer is not None:
            self.outputs["out"] = buffer[0].copy()
            return

        # If input available, infer shape and create buffer (zeros or broadcasted scalar init)
        if u is not None:
            u_arr = np.asarray(u, dtype=float)
            self._ensure_buffer_initialized(u_arr)
            self.outputs["out"] = self.state["buffer"][0].copy()
            return

        # Else defer
        self.outputs["out"] = None

    # ------------------------------------------------------------------
    def output_update(self, t: float, dt: float) -> None:
        buffer = self.state["buffer"]

        # If buffer is missing, infer from current input
        if buffer is None:
            u = self.inputs["in"]
            if u is None:
                raise RuntimeError(f"[{self.name}] Delay buffer uninitialized (no input).")
            u_arr = np.asarray(u, dtype=float)
            self._ensure_buffer_initialized(u_arr)
            buffer = self.state["buffer"]

        self.outputs["out"] = buffer[0].copy()

    # ------------------------------------------------------------------
    def state_update(self, t: float, dt: float) -> None:
        u = self.inputs["in"]
        if u is None:
            raise RuntimeError(f"[{self.name}] Input 'in' is not connected or not set.")

        u_arr = np.asarray(u, dtype=float)
        if u_arr.ndim != 2:
            raise ValueError(
                f"[{self.name}] Input 'in' must be a 2D array. Got ndim={u_arr.ndim} with shape {u_arr.shape}."
            )

        # Ensure buffer exists and matches shape (scalar-only upgrade allowed)
        self._ensure_buffer_initialized(u_arr)

        buffer = self.state["buffer"]
        assert buffer is not None  # for type checkers

        # Shift left and append current u
        new_buffer = []
        for i in range(self.num_delays - 1):
            new_buffer.append(buffer[i + 1].copy())
        new_buffer.append(u_arr.copy())

        self.next_state["buffer"] = new_buffer
