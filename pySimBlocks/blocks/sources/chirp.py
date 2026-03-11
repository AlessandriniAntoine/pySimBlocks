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

import numpy as np
from numpy.typing import ArrayLike
from pySimBlocks.core.block_source import BlockSource


class Chirp(BlockSource):
    """
    Multi-dimensional chirp signal source (linear or logarithmic).

    mode:
        "linear"      -> linear frequency sweep
        "log"         -> logarithmic (exponential) sweep
    """

    VALID_MODES = {"linear", "log"}

    def __init__(
        self,
        name: str,
        amplitude: ArrayLike,
        f0: ArrayLike,
        f1: ArrayLike,
        duration: ArrayLike,
        start_time: ArrayLike = 0.0,
        offset: ArrayLike = 0.0,
        phase: ArrayLike = 0.0,
        mode: str = "linear",
        sample_time: float | None = None,
    ):
        super().__init__(name, sample_time)

        if mode not in self.VALID_MODES:
            raise ValueError(
                f"[{name}] mode must be one of {self.VALID_MODES}"
            )

        self.mode = mode

        A = self._to_2d_array("amplitude", amplitude, dtype=float)
        F0 = self._to_2d_array("f0", f0, dtype=float)
        F1 = self._to_2d_array("f1", f1, dtype=float)
        D = self._to_2d_array("duration", duration, dtype=float)
        T0 = self._to_2d_array("start_time", start_time, dtype=float)
        O = self._to_2d_array("offset", offset, dtype=float)
        P = self._to_2d_array("phase", phase, dtype=float)

        target_shape = self._resolve_common_shape({
            "amplitude": A,
            "f0": F0,
            "f1": F1,
            "duration": D,
            "start_time": T0,
            "offset": O,
            "phase": P,
        })

        self.amplitude = self._broadcast_scalar_only("amplitude", A, target_shape)
        self.f0 = self._broadcast_scalar_only("f0", F0, target_shape)
        self.f1 = self._broadcast_scalar_only("f1", F1, target_shape)
        self.duration = self._broadcast_scalar_only("duration", D, target_shape)
        self.start_time = self._broadcast_scalar_only("start_time", T0, target_shape)
        self.offset = self._broadcast_scalar_only("offset", O, target_shape)
        self.phase = self._broadcast_scalar_only("phase", P, target_shape)

        if np.any(self.duration <= 0.0):
            raise ValueError(f"[{self.name}] duration must be > 0.")

        if self.mode == "log":
            if np.any(self.f0 <= 0.0) or np.any(self.f1 <= 0.0):
                raise ValueError(
                    f"[{self.name}] f0 and f1 must be > 0 for log mode."
                )
            if np.any(self.f0 == self.f1):
                raise ValueError(
                    f"[{self.name}] f0 must differ from f1 in log mode."
                )

        self.outputs["out"] = np.zeros(target_shape, dtype=float)

    # ------------------------------------------------------------------

    def initialize(self, t0: float) -> None:
        self._compute_output(t0)

    # ------------------------------------------------------------------

    def output_update(self, t: float, dt: float) -> None:
        self._compute_output(t)

    # ------------------------------------------------------------------

    def _compute_output(self, t: float) -> None:

        tau = np.maximum(0.0, t - self.start_time)
        tau_clip = np.minimum(tau, self.duration)

        if self.mode == "linear":
            phi = self._linear_phase(tau, tau_clip)

        else:  # log
            phi = self._log_phase(tau, tau_clip)

        self.outputs["out"] = (
            self.amplitude * np.sin(phi) + self.offset
        )

    # ------------------------------------------------------------------

    def _linear_phase(self, tau, tau_clip):

        k = (self.f1 - self.f0) / self.duration

        phi_sweep = (
            2.0 * np.pi *
            (self.f0 * tau_clip + 0.5 * k * tau_clip * tau_clip)
        )

        extra = (
            2.0 * np.pi *
            self.f1 *
            np.maximum(0.0, tau - self.duration)
        )

        return phi_sweep + extra + self.phase

    # ------------------------------------------------------------------

    def _log_phase(self, tau, tau_clip):

        ratio = self.f1 / self.f0
        log_ratio = np.log(ratio)

        coeff = 2.0 * np.pi * self.f0 * self.duration / log_ratio

        phi_sweep = coeff * (
            np.power(ratio, tau_clip / self.duration) - 1.0
        )

        # phase continuity after duration
        phi_end = coeff * (ratio - 1.0)

        extra = (
            2.0 * np.pi *
            self.f1 *
            np.maximum(0.0, tau - self.duration)
        )

        return phi_sweep + extra + self.phase
