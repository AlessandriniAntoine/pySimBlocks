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

import numpy as np
from numpy.typing import ArrayLike
from pySimBlocks.core.block_source import BlockSource


class Chirp(BlockSource):
    """Multi-dimensional chirp signal source (linear or logarithmic).

    Generates a sinusoidal signal whose frequency sweeps from f0 to f1
    over a given duration, then continues at f1. The sweep can be linear
    or logarithmic (exponential).

    Attributes:
        amplitude: Amplitude of the chirp signal, as a 2D array.
        f0: Starting frequency in Hz, as a 2D array.
        f1: Ending frequency in Hz, as a 2D array.
        duration: Sweep duration in seconds, as a 2D array.
        start_time: Time at which the chirp starts, as a 2D array.
        offset: DC offset added to the output, as a 2D array.
        phase: Initial phase in radians, as a 2D array.
        mode: Frequency sweep mode, either ``"linear"`` or ``"log"``.
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
        """Initialize a Chirp block.

        Args:
            name: Unique identifier for this block instance.
            amplitude: Amplitude of the chirp. Can be scalar, vector, or matrix.
            f0: Starting frequency in Hz. Can be scalar, vector, or matrix.
            f1: Ending frequency in Hz. Can be scalar, vector, or matrix.
            duration: Sweep duration in seconds. Can be scalar, vector, or matrix.
            start_time: Time at which the chirp starts in seconds. Can be
                scalar, vector, or matrix.
            offset: DC offset added to the output. Can be scalar, vector, or matrix.
            phase: Initial phase in radians. Can be scalar, vector, or matrix.
            mode: Frequency sweep mode. Must be ``"linear"`` or ``"log"``.
            sample_time: Sampling period in seconds, or None to use the
                global simulation dt.

        Raises:
            ValueError: If mode is not valid, duration is not strictly positive,
                or (in log mode) f0 or f1 are not strictly positive or are equal.
            ValueError: If non-scalar parameters have incompatible shapes.
        """
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


    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------

    def initialize(self, t0: float) -> None:
        """Compute and set the output at the initial time t0.

        Args:
            t0: Initial simulation time in seconds.
        """
        self._compute_output(t0)

    def output_update(self, t: float, dt: float) -> None:
        """Compute and write the chirp value to the output port.

        Args:
            t: Current simulation time in seconds.
            dt: Current time step in seconds.
        """
        self._compute_output(t)


    # --------------------------------------------------------------------------
    # Private methods
    # --------------------------------------------------------------------------

    def _compute_output(self, t: float) -> None:
        """Evaluate the chirp formula at time t and write to outputs."""
        tau = np.maximum(0.0, t - self.start_time)
        tau_clip = np.minimum(tau, self.duration)

        if self.mode == "linear":
            phi = self._linear_phase(tau, tau_clip)
        else:  # log
            phi = self._log_phase(tau, tau_clip)

        self.outputs["out"] = self.amplitude * np.sin(phi) + self.offset

    def _linear_phase(self, tau: np.ndarray, tau_clip: np.ndarray) -> np.ndarray:
        """Compute the instantaneous phase for a linear frequency sweep.

        Args:
            tau: Elapsed time since start_time, clipped to zero, as a 2D array.
            tau_clip: tau clipped to duration, as a 2D array.

        Returns:
            Instantaneous phase in radians as a 2D array.
        """
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

    def _log_phase(self, tau: np.ndarray, tau_clip: np.ndarray) -> np.ndarray:
        """Compute the instantaneous phase for a logarithmic frequency sweep.

        Args:
            tau: Elapsed time since start_time, clipped to zero, as a 2D array.
            tau_clip: tau clipped to duration, as a 2D array.

        Returns:
            Instantaneous phase in radians as a 2D array.
        """
        ratio = self.f1 / self.f0
        log_ratio = np.log(ratio)

        coeff = 2.0 * np.pi * self.f0 * self.duration / log_ratio

        phi_sweep = coeff * (
            np.power(ratio, tau_clip / self.duration) - 1.0
        )

        extra = (
            2.0 * np.pi *
            self.f1 *
            np.maximum(0.0, tau - self.duration)
        )

        return phi_sweep + extra + self.phase
