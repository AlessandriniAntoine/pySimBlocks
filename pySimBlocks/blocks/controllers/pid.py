# ******************************************************************************
#                                  pySimBlocks
#                     Copyright (c) 2026 Antoine Alessandrini
# ******************************************************************************
#  This program is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Lesser General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or (at your
#  option) any later version.
#
#  This program is distributed in the hope that it will be useful, but WITHOUT
#  ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
#  FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License
#  for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.
# ******************************************************************************
#  Authors: see Authors.txt
# ******************************************************************************

import warnings

import numpy as np
from numpy.typing import ArrayLike

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

    def __init__(
        self,
        name: str,
        controller: str = "PID",
        Kp: ArrayLike = 0.0,
        Ki: ArrayLike = 0.0,
        Kd: ArrayLike = 0.0,
        u_min: ArrayLike | None = None,
        u_max: ArrayLike | None = None,
        integration_method: str = "euler forward",
        sample_time: float | None = None,
    ):
        super().__init__(name, sample_time)

        controller = controller.upper()
        allowed_types = {"P", "I", "PI", "PD", "PID"}
        if controller not in allowed_types:
            raise ValueError(
                f"[{self.name}] Invalid controller type '{controller}'. Allowed: {allowed_types}"
            )
        self.controller = controller

        self.integration_method = integration_method.lower()
        allowed = ("euler forward", "euler backward")
        if self.integration_method not in allowed:
            raise ValueError(
                f"[{self.name}] Unsupported method '{self.integration_method}'. Allowed: {allowed}"
            )

        # Gains (SISO, (1,1))
        self.Kp = self._to_siso("Kp", Kp)
        self.Ki = self._to_siso("Ki", Ki)
        self.Kd = self._to_siso("Kd", Kd)

        self.u_min = None if u_min is None else self._to_siso("u_min", u_min)
        self.u_max = None if u_max is None else self._to_siso("u_max", u_max)

        if self.u_min is not None and self.u_max is not None:
            if float(self.u_min[0, 0]) > float(self.u_max[0, 0]):
                raise ValueError(
                    f"[{self.name}] u_min ({self.u_min.item()}) must be <= u_max ({self.u_max.item()})."
                )

        # Warnings
        self._validate_gains()

        # Direct feedthrough policy
        has_p = "P" in self.controller
        has_d = "D" in self.controller
        has_i = "I" in self.controller

        if has_p or has_d:
            self.direct_feedthrough = True
        else:
            # I-only
            self.direct_feedthrough = (self.integration_method == "euler backward")

        # Ports
        self.inputs["e"] = None
        self.outputs["u"] = None

        # State (SISO)
        self.state["x_i"] = np.zeros((1, 1), dtype=float)
        self.state["e_prev"] = np.zeros((1, 1), dtype=float)
        self.next_state["x_i"] = np.zeros((1, 1), dtype=float)
        self.next_state["e_prev"] = np.zeros((1, 1), dtype=float)


    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------
    def initialize(self, t0: float):
        # Start at zero command, keep internal states at zero.
        self.outputs["u"] = np.zeros((1, 1), dtype=float)

    # ------------------------------------------------------------------
    def output_update(self, t: float, dt: float):
        e_in = self.inputs["e"]
        if e_in is None:
            raise RuntimeError(f"[{self.name}] Missing input 'e'.")

        e = self._to_siso("e", e_in)

        x_i = self.state["x_i"]
        e_prev = self.state["e_prev"]

        has_p = "P" in self.controller
        has_i = "I" in self.controller
        has_d = "D" in self.controller

        P = self.Kp * e if has_p else np.zeros((1, 1), dtype=float)

        if has_i:
            if self.integration_method == "euler forward":
                I = x_i
            else:
                I = x_i + self.Ki * e * dt
        else:
            I = np.zeros((1, 1), dtype=float)

        D = (self.Kd * (e - e_prev) / dt) if has_d else np.zeros((1, 1), dtype=float)

        u = P + I + D

        # Saturation
        if self.u_min is not None:
            u = np.maximum(u, self.u_min)
        if self.u_max is not None:
            u = np.minimum(u, self.u_max)

        self.outputs["u"] = u

    # ------------------------------------------------------------------
    def state_update(self, t: float, dt: float):
        e_in = self.inputs["e"]
        if e_in is None:
            raise RuntimeError(f"[{self.name}] Missing input 'e'.")

        e = self._to_siso("e", e_in)

        has_i = "I" in self.controller

        # Integrator update only if I term is enabled
        if has_i:
            x_i_next = self.state["x_i"] + self.Ki * e * dt
        else:
            x_i_next = self.state["x_i"].copy()

        # Anti-windup (clamp integral state if saturation is defined)
        if self.u_min is not None:
            x_i_next = np.maximum(x_i_next, self.u_min)
        if self.u_max is not None:
            x_i_next = np.minimum(x_i_next, self.u_max)

        self.next_state["x_i"] = x_i_next
        self.next_state["e_prev"] = e.copy()


    # --------------------------------------------------------------------------
    # Private methods
    # --------------------------------------------------------------------------
    def _to_siso(self, name: str, value: ArrayLike) -> np.ndarray:
        """
        Normalize scalar-like into (1,1). Reject anything else (strict SISO).
        """
        if np.isscalar(value):
            return np.array([[float(value)]], dtype=float)

        arr = np.asarray(value, dtype=float)

        if arr.shape == ():
            return np.array([[float(arr)]], dtype=float)
        if arr.shape == (1,):
            return arr.reshape(1, 1)
        if arr.shape == (1, 1):
            return arr

        raise ValueError(
            f"[{self.name}] '{name}' must be scalar-like ((), (1,), or (1,1)). Got shape {arr.shape}."
        )

    # ------------------------------------------------------------------
    def _validate_gains(self) -> None:
        kp = float(self.Kp[0, 0])
        ki = float(self.Ki[0, 0])
        kd = float(self.Kd[0, 0])

        if "P" in self.controller and kp == 0.0:
            warnings.warn(
                f"[{self.name}] Kp=0 while controller '{self.controller}' includes a P term.",
                UserWarning,
            )
        if "I" in self.controller and ki == 0.0:
            warnings.warn(
                f"[{self.name}] Ki=0 while controller '{self.controller}' includes an I term.",
                UserWarning,
            )
        if "D" in self.controller and kd == 0.0:
            warnings.warn(
                f"[{self.name}] Kd=0 while controller '{self.controller}' includes a D term.",
                UserWarning,
            )
