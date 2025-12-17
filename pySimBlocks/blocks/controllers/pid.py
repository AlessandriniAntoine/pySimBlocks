import numpy as np
import warnings
from pySimBlocks.core.block import Block


class Pid(Block):
    """
    Discrete-time PID controller block.

    Summary:
        Implements a single-input single-output discrete PID controller,
        similar to the Simulink PID block. The controller computes a control
        command from an error signal using proportional, integral and/or
        derivative actions, depending on the selected control mode.

    Parameters (overview):
        controller : str
            Control mode. One of {"P", "PI", "PD", "PID"}.
        Kp : float
            Proportional gain.
        Ki : float
            Integral gain.
        Kd : float
            Derivative gain.
        u_min : float, optional
            Minimum output saturation.
        u_max : float, optional
            Maximum output saturation.
        sample_time : float, optional
            Controller sampling period.

    I/O:
        Inputs:
            e : error signal.
        Outputs:
            u : control command.

    Notes:
        - The block is strictly SISO.
        - Integral action introduces internal state.
        - If a parameter is not provided, the block falls back to its
          internal default value.
        - Output saturation is applied only if u_min and/or u_max are defined.
    """



    # ---------------------------------------------------------------------
    def __init__(self,
                 name: str, controller:str = "PID",
                 Kp=0.0, Ki=0.0, Kd=0.0,
                 u_min=None, u_max=None,
                 integration_method:str = 'euler forward',
                 sample_time:float|None = None):

        super().__init__(name, sample_time)

        # -------------------------
        # Validate controller type
        # -------------------------
        controller = controller.upper()
        allowed_types = {"P", "I", "PI", "PD", "PID"}
        if controller not in allowed_types:
            raise ValueError(
                f"[{name}] Invalid controller type '{controller}'. "
                f"Allowed: {allowed_types}"
            )
        self.controller = controller

        # -------------------------------
        # 1) Validate and normalize gains
        # -------------------------------
        self.Kp = self._normalize_and_check_gain(Kp, "Kp")
        self.Ki = self._normalize_and_check_gain(Ki, "Ki")
        self.Kd = self._normalize_and_check_gain(Kd, "Kd")

        # -------------------------
        # Validate required gains
        # -------------------------
        self._validate_gains()

        # -------------------------------
        # 2) Validate saturation bounds
        # -------------------------------
        if u_min is not None:
            self.u_min = self._normalize_and_check_scalar(u_min, "u_min")
        else:
            self.u_min = None

        if u_max is not None:
            self.u_max = self._normalize_and_check_scalar(u_max, "u_max")
        else:
            self.u_max = None

        if self.u_min is not None and self.u_max is not None:
            if self.u_min > self.u_max:
                raise ValueError(
                    f"[{self.name}] u_min ({self.u_min}) must be <= u_max ({self.u_max})."
                )

        # ---------------------------------
        # Validate method
        # ---------------------------------
        self.integration_method = integration_method.lower()
        allowed = ("euler forward", "euler backward")
        if self.integration_method not in allowed:
            raise ValueError(
                f"[{self.name}] Unsupported method '{self.integration_method}'. "
                f"Allowed: {allowed}"
            )

        # specify feedthrough
        if self.controller == "I" and self.integration_method == "euler forward":
            self.direct_feedthrough = False

        # -------------------------------
        # 3) Declare ports
        # -------------------------------
        self.inputs["e"] = None
        self.outputs["u"] = None

        # -------------------------------
        # 4) Internal state (SISO → always (1,1))
        # -------------------------------
        self.state["x_i"] = np.zeros((1,1))     # integral state
        self.state["e_prev"] = np.zeros((1,1))  # previous error

        self.next_state["x_i"] = np.zeros((1,1))
        self.next_state["e_prev"] = np.zeros((1,1))


    # =====================================================================
    #  Utility: Normalize a scalar-like value and check it is SISO
    # =====================================================================
    def _normalize_and_check_gain(self, value, name):
        """Convert float/list/array to (1,1) ndarray. Reject anything else."""
        # float
        if np.isscalar(value):
            return np.array([[float(value)]])

        arr = np.asarray(value)

        # numpy scalar
        if arr.shape == ():
            return np.array([[float(arr)]])

        # vector of length 1
        if arr.shape == (1,):
            return arr.reshape((1,1))

        # already (1,1)
        if arr.shape == (1,1):
            return arr

        raise ValueError(
            f"[{self.name}] Gain '{name}' must be scalar-like (float, list of length 1, "
            f"array of shape (1,), or (1,1)). Received shape {arr.shape}."
        )

    def _normalize_and_check_scalar(self, value, name):
        """Normalize a scalar-like parameter for saturations."""
        if np.isscalar(value):
            return np.array([[float(value)]])

        arr = np.asarray(value)
        if arr.shape == ():
            return np.array([[float(arr)]])
        if arr.shape == (1,):
            return arr.reshape(1,1)
        if arr.shape == (1,1):
            return arr

        raise ValueError(
            f"[{self.name}] Parameter '{name}' must be scalar-like. Received shape {arr.shape}."
        )

    def _validate_gains(self):
        if self.controller in {"P", "PI", "PID", "PD"} and self.Kp == 0:
            warnings.warn(
                f"[{self.name}] Kp=0 while controller '{self.controller}' includes a P term.",
                UserWarning
            )

        if self.controller in {"I", "PI", "PID"} and self.Ki == 0:
            warnings.warn(
                f"[{self.name}] Ki=0 while controller '{self.controller}' includes a I term.",
                UserWarning
            )

        if self.controller in {"PD", "PID"} and self.Kd == 0:
            warnings.warn(
                f"[{self.name}] Kd=0 while controller '{self.controller}' includes a D term.",
                UserWarning
            )

    # =====================================================================
    # Initialization
    # =====================================================================
    def initialize(self, t0: float):
        # PID outputs start at zero
        self.outputs["u"] = np.zeros((1,1))

    # =====================================================================
    # Phase 1 : output_update
    # =====================================================================
    def output_update(self, t: float, dt: float):
        e = self.inputs["e"]
        if e is None:
            raise RuntimeError(f"[{self.name}] Missing input 'e'.")
        e = np.asarray(e).reshape(1,1)

        x_i = self.state["x_i"]
        e_prev = self.state["e_prev"]

        # P, I, D terms
        P = self.Kp * e
        if self.integration_method == "euler forward":
            I = x_i
        elif self.integration_method == "euler backward":
            I = x_i + self.Ki * e * dt

        D = self.Kd * (e - e_prev) / dt

        u = P + I + D

        # Apply saturation
        if self.u_min is not None:
            u = np.maximum(u, self.u_min)
        if self.u_max is not None:
            u = np.minimum(u, self.u_max)

        self.outputs["u"] = u

    # =====================================================================
    # Phase 2 : state_update
    # =====================================================================
    def state_update(self, t: float, dt: float):
        e = np.asarray(self.inputs["e"]).reshape(1,1)

        # Integrator update
        if self.integration_method == "euler forward":
            x_i_next = self.state["x_i"] + self.Ki * e * dt
        elif self.integration_method == "euler backward":
            x_i_next = self.outputs["u"] - (self.Kp * e + self.Kd * (e - self.state["e_prev"]) / dt)

        # Anti-windup: clamp integral state
        if self.u_min is not None:
            x_i_next = np.maximum(x_i_next, self.u_min)
        if self.u_max is not None:
            x_i_next = np.minimum(x_i_next, self.u_max)

        self.next_state["x_i"] = x_i_next
        self.next_state["e_prev"] = e.copy()
