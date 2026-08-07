# ******************************************************************************
#                                  pySimBlocks
#                     Copyright (c) 2026 Université de Lille & INRIA
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

from __future__ import annotations

from typing import Literal

import numpy as np
from numpy.typing import ArrayLike

from pySimBlocks.core.block import Block


class TransferFunction(Block):
    """SISO transfer-function block, executed as a discrete-time state-space system.

    Realizes H(s)=num/den or H(z)=num/den as a companion-form state-space
    system and, if continuous, discretizes it into:

        x[k+1] = A x[k] + B u[k]
        y[k]   = C x[k] + D u[k]

    num/den are coefficient lists in decreasing powers, e.g. for
    H(s) = (2s + 3) / (s^2 + 4s + 5): num=[2, 3], den=[1, 4, 5].

    For domain="continuous", discretization happens lazily in initialize()
    once Ts (explicit sample_time, or else the global simulation dt) is
    known -- see initialize() for why.

    Attributes:
        num: Numerator coefficients as provided, decreasing powers.
        den: Denominator coefficients as provided, decreasing powers.
        domain: "continuous" or "discrete", the domain of num/den.
        discretization: Method used when domain is "continuous".
        A: Discrete-time state transition matrix actually executed.
        B: Discrete-time input matrix actually executed.
        C: Discrete-time output matrix actually executed.
        D: Discrete-time feedthrough matrix actually executed.
    """

    # Default at class level; overridden per-instance once D is known.
    direct_feedthrough = False

    def __init__(
        self,
        name: str,
        num: ArrayLike,
        den: ArrayLike,
        domain: Literal["continuous", "discrete"] = "discrete",
        discretization: Literal["tustin", "zoh"] = "tustin",
        x0: ArrayLike | None = None,
        sample_time: float | None = None,
    ):
        """Initialize a TransferFunction block.

        Args:
            name: Unique identifier for this block instance.
            num: Numerator coefficients, highest power first.
            den: Denominator coefficients, highest power first.
            domain: "continuous" (s) or "discrete" (z) domain of num/den.
            discretization: "tustin" (NumPy only) or "zoh" (requires scipy).
                Used only when domain="continuous".
            x0: Initial state vector, array-like of shape (n, 1) or (n,).
                Defaults to zeros.
            sample_time: Sampling period in seconds. Required when
                domain="continuous" (used as the discretization period Ts).
                Optional when domain="discrete" (falls back to the global
                simulation dt).

        Raises:
            ValueError: If den is zero, if num/den is improper, if domain
                or discretization is invalid, or if x0 has the wrong shape.
            ImportError: If discretization="zoh" is requested without scipy.
        """
        super().__init__(name, sample_time)

        self.num = np.atleast_1d(np.asarray(num, dtype=float))
        self.den = np.atleast_1d(np.asarray(den, dtype=float))
        self.domain = domain
        self.discretization = discretization

        if self.den.size == 0 or np.all(self.den == 0):
            raise ValueError(f"[{self.name}] 'den' must be a non-zero polynomial.")
        if self.num.size > self.den.size:
            raise ValueError(
                f"[{self.name}] Improper transfer function: "
                f"deg(num)={self.num.size - 1} > deg(den)={self.den.size - 1}."
            )
        if domain not in ("continuous", "discrete"):
            raise ValueError(
                f"[{self.name}] 'domain' must be 'continuous' or 'discrete'. Got {domain!r}."
            )
        if discretization not in ("tustin", "zoh"):
            raise ValueError(
                f"[{self.name}] 'discretization' must be 'tustin' or 'zoh'. Got {discretization!r}."
            )

        # Normalize so den is monic; H(s) = num/den is unchanged.
        den_monic = self.den / self.den[0]
        num_monic = self.num / self.den[0]

        A0, B0, C0, D0 = self._tf2ss_companion(num_monic, den_monic)
        n = A0.shape[0]
        self._n = n
        self._m = B0.shape[1]
        self._p = C0.shape[0]

        if domain == "discrete" or n == 0:
            # Ready immediately: nothing to discretize (already in z, or a
            # pure static gain for which s/z make no difference).
            self.A, self.B, self.C, self.D = A0, B0, C0, D0
            self._pending_discretization = False
            has_feedthrough = bool(np.any(D0 != 0))
        else:
            # domain="continuous" with dynamics: the numeric discretization
            # needs a concrete Ts, which may only come from the *global*
            # simulation dt -- resolved by the Simulator well after this
            # constructor runs. So A/B/C/D are computed lazily in
            # initialize(), once self._effective_sample_time is available
            # (same pattern as SofaPlant).
            self.A = self.B = self.C = self.D = None
            self._A0, self._B0, self._C0, self._D0 = A0, B0, C0, D0
            self._pending_discretization = True

            # direct_feedthrough still has to be known *now*: it is read by
            # build_execution_order() for algebraic-loop detection, which
            # runs before sample times are resolved. It can be decided
            # without knowing Ts:
            #   - ZOH preserves D exactly (Dd = D0), independent of Ts.
            #   - Tustin adds C(I-A*Ts/2)^-1 B * Ts/2, generically non-zero
            #     for any dynamic system regardless of Ts.
            if discretization == "zoh":
                has_feedthrough = bool(np.any(D0 != 0))
            else:
                has_feedthrough = True

        if has_feedthrough:
            self.direct_feedthrough = True

        # --- Initial state ---
        if x0 is None:
            x0_arr = np.zeros((n, 1), dtype=float)
        else:
            x0_arr = np.asarray(x0, dtype=float)
            if x0_arr.ndim == 0:
                x0_arr = x0_arr.reshape(1, 1)
            elif x0_arr.ndim == 1:
                x0_arr = x0_arr.reshape(-1, 1)
            elif x0_arr.ndim != 2:
                raise ValueError(f"[{self.name}] x0 must be 1D or 2D. Got shape {x0_arr.shape}.")

            if x0_arr.shape != (n, 1):
                raise ValueError(f"[{self.name}] x0 must have shape ({n}, 1). Got {x0_arr.shape}.")

        self.state["x"] = x0_arr.copy()
        self.next_state["x"] = x0_arr.copy()

        self.inputs["u"] = None
        self.outputs["y"] = None
        self.outputs["x"] = None


    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------

    def initialize(self, t0: float) -> None:
        """Resolve pending discretization, then compute initial outputs.

        Args:
            t0: Initial simulation time in seconds.

        Raises:
            RuntimeError: If domain="continuous" and no discretization
                period could be resolved (no explicit sample_time and the
                block is not driven by a Model/Simulator).
        """
        if self._pending_discretization:
            Ts = self.sample_time if self.sample_time is not None else self._effective_sample_time
            if Ts is None or Ts <= 0:
                raise RuntimeError(
                    f"[{self.name}] Could not resolve a discretization period for "
                    f"domain='continuous': pass 'sample_time' explicitly, or run "
                    f"this block inside a Model/Simulator so the global dt is used."
                )
            if self.discretization == "tustin":
                self.A, self.B, self.C, self.D = self._c2d_tustin(
                    self._A0, self._B0, self._C0, self._D0, Ts
                )
            else:
                self.A, self.B, self.C, self.D = self._c2d_zoh(
                    self._A0, self._B0, self._C0, self._D0, Ts
                )
            self._pending_discretization = False

        x = self.state["x"]
        self.outputs["y"] = self.C @ x
        self.outputs["x"] = x.copy()
        self.next_state["x"] = x.copy()

    def output_update(self, t: float, dt: float) -> None:
        """Compute y and x outputs from the committed state.

        When D is non-zero, u[k] is read at this step (direct feedthrough).

        Args:
            t: Current simulation time in seconds.
            dt: Current time step in seconds.
        """
        x = self.state["x"]
        if np.any(self.D != 0):
            u = self.inputs["u"]
            if u is None:
                raise RuntimeError(f"[{self.name}] Input 'u' is not connected or not set.")
            u_vec = self._to_col_vec("u", u, self._m)
            self.outputs["y"] = self.C @ x + self.D @ u_vec
        else:
            self.outputs["y"] = self.C @ x
        self.outputs["x"] = x.copy()

    def state_update(self, t: float, dt: float) -> None:
        """Compute the next state x[k+1] = A x[k] + B u[k].

        Args:
            t: Current simulation time in seconds.
            dt: Current time step in seconds.

        Raises:
            RuntimeError: If input 'u' is not connected.
            ValueError: If input 'u' has the wrong shape.
        """
        u = self.inputs["u"]
        if u is None:
            raise RuntimeError(f"[{self.name}] Input 'u' is not connected or not set.")

        u_vec = self._to_col_vec("u", u, self._m)
        x = self.state["x"]

        self.next_state["x"] = self.A @ x + self.B @ u_vec


    # --------------------------------------------------------------------------
    # Private methods
    # --------------------------------------------------------------------------

    def _tf2ss_companion(
        self, num: np.ndarray, den: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Build a controllable-canonical realization from monic num/den.

        Returns:
            (A, B, C, D). n == 0 (constant den, i.e. a pure gain) yields
            empty A/B/C and a scalar D.
        """
        n = den.size - 1

        if n == 0:
            D = np.array([[num[0]]], dtype=float)
            A = np.zeros((0, 0))
            B = np.zeros((0, 1))
            C = np.zeros((1, 0))
            return A, B, C, D

        num_padded = np.zeros(n + 1)
        num_padded[-num.size:] = num

        a = den[1:]      # a1..an
        b = num_padded   # b0..bn

        A = np.zeros((n, n))
        A[0, :] = -a
        if n > 1:
            A[1:, :-1] = np.eye(n - 1)

        B = np.zeros((n, 1))
        B[0, 0] = 1.0

        D = np.array([[b[0]]])

        C = np.zeros((1, n))
        for i in range(n):
            C[0, i] = b[i + 1] - b[0] * a[i]

        return A, B, C, D

    def _c2d_tustin(
        self,
        A: np.ndarray,
        B: np.ndarray,
        C: np.ndarray,
        D: np.ndarray,
        Ts: float,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Discretize (A, B, C, D) with the bilinear (Tustin) transform.

        Returns:
            Discrete-time (Ad, Bd, Cd, Dd) matrices.
        """
        n = A.shape[0]
        if n == 0:
            return A, B, C, D

        I = np.eye(n)
        M_inv = np.linalg.inv(I - A * Ts / 2)

        Ad = M_inv @ (I + A * Ts / 2)
        Bd = (M_inv @ B) * Ts
        Cd = C @ M_inv
        Dd = D + (C @ M_inv @ B) * (Ts / 2)

        return Ad, Bd, Cd, Dd

    def _c2d_zoh(
        self,
        A: np.ndarray,
        B: np.ndarray,
        C: np.ndarray,
        D: np.ndarray,
        Ts: float,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Discretize (A, B, C, D) with zero-order-hold, via a lazy scipy import.

        Raises:
            ImportError: If scipy is not installed.
        """
        n = A.shape[0]
        if n == 0:
            return A, B, C, D

        try:
            from scipy.signal import cont2discrete
        except ImportError as e:
            raise ImportError(
                f"[{self.name}] discretization='zoh' requires the optional 'scipy' "
                f"dependency. Install it with `pip install scipy`, or use "
                f"discretization='tustin' instead (no extra dependency)."
            ) from e

        Ad, Bd, Cd, Dd, _ = cont2discrete((A, B, C, D), Ts, method="zoh")
        return Ad, Bd, Cd, Dd

    def _to_col_vec(self, name: str, value: ArrayLike, expected_rows: int) -> np.ndarray:
        """Normalize value to a (n,1) column vector and validate its size."""
        arr = np.asarray(value, dtype=float)

        if arr.ndim == 0:
            arr = arr.reshape(1, 1)
        elif arr.ndim == 1:
            arr = arr.reshape(-1, 1)
        elif arr.ndim == 2:
            pass
        else:
            raise ValueError(f"[{self.name}] {name} must be 1D or 2D. Got shape {arr.shape}.")

        if arr.shape[1] != 1:
            raise ValueError(f"[{self.name}] {name} must be a column vector (k,1). Got {arr.shape}.")

        if arr.shape[0] != expected_rows:
            raise ValueError(
                f"[{self.name}] {name} must have shape ({expected_rows},1). Got {arr.shape}."
            )

        return arr
