import numpy as np
from pySimBlocks.core.block import Block


class DiscreteDerivator(Block):
    """
    Discrete-time differentiator block.

    Summary:
        Estimates the discrete-time derivative of the input signal using a
        backward finite difference.

    Parameters (overview):
        initial_output : scalar or vector, optional
            Initial derivative value at the first time step.
        sample_time : float, optional
            Block execution period.

    I/O:
        Inputs:
            in : Input signal.
        Outputs:
            out : Estimated discrete-time derivative.

    Notes:
        - Stateful block.
        - Direct feedthrough.
        - Uses a backward difference scheme consistent with Simulink discrete
          Derivative behavior.
        - Output dimension is inferred from the first valid input.
    """


    def __init__(self, name: str, initial_output=None, sample_time:float|None = None):
        super().__init__(name, sample_time)

        self.inputs["in"] = None
        self.outputs["out"] = None

        self.state["u_prev"] = None
        self.next_state["u_prev"] = None

        self._first_output = True

        if initial_output is not None:
            arr = np.asarray(initial_output)
            if arr.ndim == 0:
                arr = arr.reshape(1,1)
            elif arr.ndim == 1:
                arr = arr.reshape(-1,1)
            elif arr.ndim == 2 and arr.shape[1] == 1:
                pass
            else:
                raise ValueError(...)
            self.outputs["out"] = arr.copy()
        else:
            self.outputs["out"] = None

    # -------------------------------------------------------
    def initialize(self, t0: float):
        """
        Initialization rules:

        - If initial_output is provided → keep it as y[0].
        - If input u(0) exists → set u_prev = u(0).
        - If no input yet → u_prev stays None.
        """

        u = self.inputs["in"]

        # If input exists, normalize it
        if u is not None:
            u = np.asarray(u)
            if u.ndim != 2 or u.shape[1] != 1:
                raise ValueError(
                    f"[{self.name}] Input 'in' must be column vector (n,1). Got {u.shape}."
                )
            u = u.reshape(-1, 1)

            # store u_prev (even if initial_output is provided)
            self.state["u_prev"] = u.copy()
            self.next_state["u_prev"] = u.copy()

            # If no IC → default derivative = zero
            if self.outputs["out"] is None:
                self.outputs["out"] = np.zeros_like(u)

        # Case: no input available yet
        else:
            # If IC exists: outputs["out"] already set → keep it
            # Else: output stays None until an input appears
            self.state["u_prev"] = None
            self.next_state["u_prev"] = None


    # -------------------------------------------------------
    def output_update(self, t: float, dt: float):
        """
        y[k] = (u[k] - u[k-1]) / dt
        """
        if self._first_output:
            self._first_output = False
            return

        u = self.inputs["in"]
        if u is None:
            raise RuntimeError(f"[{self.name}] Input 'in' not set.")

        u = np.asarray(u)
        if u.ndim != 2 or u.shape[1] != 1:
            raise ValueError(
                f"[{self.name}] Input 'in' must be column vector (n,1). Got {u.shape}."
            )

        u = u.reshape(-1, 1)
        u_prev = self.state["u_prev"]

        # If no previous value → derivative = zero
        if u_prev is None:
            self.outputs["out"] = np.zeros_like(u)
            return

        # Dim mismatch
        if u.shape != u_prev.shape:
            raise ValueError(
                f"[{self.name}] Input dimension {u.shape} incompatible with "
                f"previous input dimension {u_prev.shape}."
            )

        y = (u - u_prev) / dt
        self.outputs["out"] = y

    # -------------------------------------------------------
    def state_update(self, t: float, dt: float):
        """
        Update previous input.
        """
        u = self.inputs["in"]
        if u is None:
            raise RuntimeError(f"[{self.name}] Input 'in' not set.")

        u = np.asarray(u)
        if u.ndim != 2 or u.shape[1] != 1:
            raise ValueError(
                f"[{self.name}] Input 'in' must be column vector (n,1). Got {u.shape}."
            )

        u = u.reshape(-1, 1)
        u_prev = self.state["u_prev"]

        # Check mismatch AFTER u is reshaped
        if u_prev is not None and u.shape != u_prev.shape:
            raise ValueError(
                f"[{self.name}] Input dimension {u.shape} incompatible with "
                f"previous input dimension {u_prev.shape}."
            )

        self.next_state["u_prev"] = u.copy()
