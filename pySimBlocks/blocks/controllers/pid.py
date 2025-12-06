import numpy as np
from pySimBlocks.core.block import Block


class Pid(Block):
    """
    General discrete PID controller with selectable mode (P, PI, PD, ID, PID).

    Implements:

        u[k] = Kp * e[k]
             + Ki * x_i[k]
             + Kd * (e[k] - e[k-1]) / dt

        x_i[k+1] = x_i[k] + e[k] * dt

    Parameters:
        name: str
            Block name.

        controller_type: str
            One of: "P", "PI", "PD", "ID", "PID".
            Determines which gains are active.

        Kp: array (m,n) (optional)
            Proportional gain matrix.

        Ki: array (m,n) (optional)
            Integral gain matrix.

        Kd: array (m,n) (optional)
            Derivative gain matrix.

        u_min: array (m,1) (optional)
            Minimum output saturation.

        u_max: array (m,1) (optional)
            Maximum output saturation.

    Inputs:
        e: array (n,1)
            Error signal.

    Outputs:
        u: array (m,1)
            Control command.
    """

    VALID_TYPES = ["P", "PI", "PD", "ID", "PID"]

    def __init__(self,
                 name: str,
                 controller_type: str = "P",
                 Kp=None, Ki=None, Kd=None,
                 u_min=None, u_max=None):

        super().__init__(name)

        # Validate type
        if controller_type not in self.VALID_TYPES:
            raise ValueError(
                f"Invalid controller_type '{controller_type}'. "
                f"Must be one of {self.VALID_TYPES}."
            )
        self.controller_type = controller_type

        # Kp/Ki/Kd optional — depending on type
        self.Kp = np.asarray(Kp) if Kp is not None else None
        self.Ki = np.asarray(Ki) if Ki is not None else None
        self.Kd = np.asarray(Kd) if Kd is not None else None

        # Activation rules
        need_Kp = controller_type in ["P", "PI", "PD", "PID"]
        need_Ki = controller_type in ["PI", "ID", "PID"]
        need_Kd = controller_type in ["PD", "ID", "PID"]

        if need_Kp and self.Kp is None:
            raise ValueError("Kp must be provided for controller_type requiring proportional action.")
        if need_Ki and self.Ki is None:
            raise ValueError("Ki must be provided for controller_type requiring integral action.")
        if need_Kd and self.Kd is None:
            raise ValueError("Kd must be provided for controller_type requiring derivative action.")

        if self.Kp is not None:
            m, n = self.Kp.shape
        elif self.Ki is not None:
            m, n = self.Ki.shape
        elif self.Kd is not None:
            m, n = self.Kd.shape
        else:
            raise RuntimeError("At least one gain (Kp, Ki, or Kd) must be provided.")

        # Missing gains replaced with zero matrices
        # → allows unified formula regardless of type
        if self.Kp is None:
            self.Kp = np.zeros((m,n))
        if self.Ki is None:
            self.Ki = np.zeros((m,n))
        if self.Kd is None:
            self.Kd = np.zeros((m,n))

        # Optional saturation
        self.u_min = None if u_min is None else np.asarray(u_min).reshape(-1,1)
        self.u_max = None if u_max is None else np.asarray(u_max).reshape(-1,1)

        # Ports
        self.inputs["e"] = None
        self.outputs["u"] = None

        # Internal states
        self.state["x_i"] = None
        self.state["e_prev"] = None
        self.next_state["x_i"] = None
        self.next_state["e_prev"] = None


    # -------------------------------------------------------
    def initialize(self, t0: float):
        # Determine sizes automatically from Kp
        # (safe since gains must exist when needed)
        if isinstance(self.Kp, np.ndarray):
            m, n = self.Kp.shape
        else:
            raise RuntimeError("PID gains are not initialized properly.")

        self.state["x_i"] = np.zeros((m,1))
        self.state["e_prev"] = np.zeros((n,1))

        self.next_state["x_i"] = self.state["x_i"].copy()
        self.next_state["e_prev"] = self.state["e_prev"].copy()

        self.outputs["u"] = np.zeros((m,1))


    # -------------------------------------------------------
    def output_update(self, t: float):
        e = self.inputs["e"]
        if e is None:
            raise RuntimeError(f"[{self.name}] Input 'e' missing at t={t}.")
        e = np.asarray(e).reshape(-1,1)

        x_i = self.state["x_i"]
        e_prev = self.state["e_prev"]

        # unified PID formula (gains may be zero)
        u = (self.Kp @ e
             + self.Ki @ x_i
             + self.Kd @ (e - e_prev))

        # saturation
        if self.u_min is not None:
            u = np.maximum(u, self.u_min)
        if self.u_max is not None:
            u = np.minimum(u, self.u_max)

        self.outputs["u"] = u


    # -------------------------------------------------------
    def state_update(self, t: float, dt: float):
        e = np.asarray(self.inputs["e"]).reshape(-1,1)

        x_i = self.state["x_i"] + e * dt

        # anti-windup via clamping
        if self.u_min is not None:
            x_i = np.maximum(x_i, self.u_min)
        if self.u_max is not None:
            x_i = np.minimum(x_i, self.u_max)

        self.next_state["x_i"] = x_i
        self.next_state["e_prev"] = e.copy()
