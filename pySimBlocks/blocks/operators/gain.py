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

import re
import unicodedata

import numpy as np
from numpy.typing import ArrayLike

from pySimBlocks.core.block import Block


class Gain(Block):
    """
    Static gain block.

    Summary:
        Applies a gain to the input signal according to the selected multiplication mode.

    Parameters:
        gain: scalar, vector (m,), or matrix (m,n)
            Gain coefficient(s).
        multiplication: str
            One of:
              - "Element wise (K * u)"
              - "Matrix (K @ u)"
              - "Matrix (u @ K)"
        sample_time: float, optional
            Block execution period.

    Inputs:
        in: array (r,c)
            Input signal (must be 2D).

    Outputs:
        out: array
            Output signal (2D), depending on multiplication mode.
    """

    direct_feedthrough = True

    MULT_ELEMENTWISE = "Element wise (K * u)"
    MULT_LEFT = "Matrix (K @ u)"
    MULT_RIGHT = "Matrix (u @ K)"
    ALLOWED_MULTIPLICATIONS = {MULT_ELEMENTWISE, MULT_LEFT, MULT_RIGHT}

    def __init__(
        self,
        name: str,
        gain: ArrayLike = 1.0,
        multiplication: str = MULT_ELEMENTWISE,
        sample_time: float | None = None,
    ):
        super().__init__(name, sample_time)

        self.multiplication = self._parse_multiplication(multiplication)

        # Normalize gain
        if np.isscalar(gain):
            self.gain = float(gain)
            self._gain_kind = "scalar"
        else:
            g = np.asarray(gain, dtype=float)
            if g.ndim not in (1, 2):
                raise ValueError(
                    f"[{self.name}] 'gain' must be a scalar, 1D vector, or 2D matrix. "
                    f"Got ndim={g.ndim} with shape {g.shape}."
                )
            self.gain = g
            self._gain_kind = "vector" if g.ndim == 1 else "matrix"

        self.inputs["in"] = None
        self.outputs["out"] = None

    # --------------------------------------------------------------------------
    # Class methods
    # --------------------------------------------------------------------------
    @classmethod
    def _parse_multiplication(cls, multiplication: str) -> str:
        if not isinstance(multiplication, str):
            raise TypeError(f"[{cls.__name__}] 'multiplication' must be a str.")

        m = cls._normalize_user_string(multiplication)

        # --- Element-wise
        if m in {
            "elementwise(k*u)", "elementwise", "elem", "k*u", "*", "k×u", "kxu"
        }:
            return cls.MULT_ELEMENTWISE

        # --- Left: K @ u
        if m in {
            "matrix(k@u)", "k@u", "left", "matleft", "@left"
        }:
            return cls.MULT_LEFT

        # --- Right: u @ K
        if m in {
            "matrix(u@k)", "u@k", "right", "matright", "@right"
        }:
            return cls.MULT_RIGHT

        # fallback pattern-based (tolère "matrix(...)" etc.)
        if "k@u" in m:
            return cls.MULT_LEFT
        if "u@k" in m:
            return cls.MULT_RIGHT

        raise ValueError(
            f"[{cls.__name__}] Invalid 'multiplication'='{multiplication}'. "
            f"Examples: '{cls.MULT_ELEMENTWISE}', '{cls.MULT_RIGHT}', '{cls.MULT_LEFT}'."
        )

    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------
    def initialize(self, t0: float) -> None:
        u = self.inputs["in"]
        if u is None:
            self.outputs["out"] = None
            return

        if not self._gain_kind == "scalar":
            if u.ndim == 1 and u.shape[0] == 1:
                u = self._resolve_initialize(u)
            if u.ndim == 2 and u.shape == (1, 1):
                u = self._resolve_initialize(u)

        self.outputs["out"] = self._compute(u)

    # ------------------------------------------------------------------
    def output_update(self, t: float, dt: float) -> None:
        u = self.inputs["in"]
        if u is None:
            raise RuntimeError(f"[{self.name}] Input 'in' is not connected or not set.")
        self.outputs["out"] = self._compute(u)

    # ------------------------------------------------------------------
    def state_update(self, t: float, dt: float) -> None:
        return  # stateless


    # --------------------------------------------------------------------------
    # Private methods
    # --------------------------------------------------------------------------
    @staticmethod
    def _normalize_user_string(s: str) -> str:
        s = unicodedata.normalize("NFKC", s)
        s = s.strip().lower()
        s = s.replace("\u00A0", " ")
        s = re.sub(r"\s+", "", s, flags=re.UNICODE)
        return s

    # ------------------------------------------------------------------
    def _resolve_initialize(self, u) -> np.ndarray:
        u = u.flatten()
        if self.multiplication != self.MULT_ELEMENTWISE:
            u = np.full((self.gain.shape[1], 1), u[0], dtype=float)
        elif self.multiplication == self.MULT_ELEMENTWISE:
            if self._gain_kind == "vector":
                u = np.full((self.gain.shape[0], 1), u[0], dtype=float)
            elif self._gain_kind == "matrix":
                u = np.full(self.gain.shape, u[0], dtype=float)
        return u

    # ------------------------------------------------------------------
    def _compute(self, u) -> np.ndarray:
        u = np.asarray(u, dtype=float)
        if u.ndim != 2:
            raise ValueError(
                f"[{self.name}] Input 'in' must be a 2D array. Got ndim={u.ndim} with shape {u.shape}."
            )

        if self.multiplication == self.MULT_ELEMENTWISE:
            return self._elementwise(u)

        if self.multiplication == self.MULT_LEFT:
            return self._left_multiply(u)

        if self.multiplication == self.MULT_RIGHT:
            return self._right_multiply(u)

        # Should be impossible due to validation in __init__
        raise RuntimeError(f"[{self.name}] Unhandled multiplication mode: {self.multiplication}")

    # ------------------------------------------------------------------
    def _elementwise(self, u: np.ndarray) -> np.ndarray:
        """
        Element-wise multiplication: K * u

        Rules:
            - scalar K: y = K * u
            - vector K (m,): y = K[:,None] * u, requires u.shape[0] == m
            - matrix K (m,n): y = K * u, requires u.shape == (m,n)
        """
        if self._gain_kind == "scalar":
            return self.gain * u

        if self._gain_kind == "vector":
            g = self.gain  # shape (m,)
            if g.shape[0] != 1 and u.shape[0] != g.shape[0]:
                raise ValueError(
                    f"[{self.name}] Element-wise mode requires u.shape[0] == len(gain). "
                    f"Got u.shape={u.shape}, gain.shape={g.shape}."
                )
            return g.reshape(-1, 1) * u

        # matrix gain
        g = self.gain
        if not self._is_scalar_2d(g) and u.shape != g.shape:
            raise ValueError(
                f"[{self.name}] Element-wise mode with matrix gain requires u.shape == gain.shape. "
                f"Got u.shape={u.shape}, gain.shape={g.shape}."
            )
        return g * u

    # ------------------------------------------------------------------
    def _left_multiply(self, u: np.ndarray) -> np.ndarray:
        """
        Matrix multiplication: K @ u

        Rules:
            - K must be 2D matrix (p,m)
            - u must be 2D (m,ncols)
            - output is (p,ncols)
        """
        if self._gain_kind != "matrix":
            raise ValueError(
                f"[{self.name}] Multiplication mode '{self.MULT_LEFT}' requires a 2D matrix gain. "
                f"Got gain kind '{self._gain_kind}'."
            )

        K = self.gain
        p, m = K.shape
        if u.shape[0] != m:
            raise ValueError(
                f"[{self.name}] Left matrix product requires u.shape[0] == gain.shape[1]. "
                f"Got u.shape={u.shape}, gain.shape={K.shape}."
            )
        return K @ u

    # ------------------------------------------------------------------
    def _right_multiply(self, u: np.ndarray) -> np.ndarray:
        """
        Matrix multiplication: u @ K

        Rules:
            - K must be 2D matrix (m,q)
            - u must be 2D (nrows,m)
            - output is (nrows,q)
        """

        if self._gain_kind != "matrix":
            raise ValueError(
                f"[{self.name}] Multiplication mode '{self.MULT_RIGHT}' requires a 2D matrix gain. "
                f"Got gain kind '{self._gain_kind}'."
            )

        K = self.gain
        m, q = K.shape

        # --- Special case: u is a vector (n,1)
        if u.shape[1] == 1:
            if u.shape[0] != m:
                raise ValueError(
                    f"[{self.name}] Right matrix product with vector requires u.shape[0] == gain.shape[0]."
                    f"Got u.shape={u.shape}, gain.shape={K.shape}."
                )
            return (u.T @ K).T

        # --- General case: u is a matrix (nrows,m)
        if u.shape[1] != m:
            raise ValueError(
                f"[{self.name}] Right matrix product requires u.shape[1] == gain.shape[0]. "
                f"Got u.shape={u.shape}, gain.shape={K.shape}."
            )
        return u @ K
