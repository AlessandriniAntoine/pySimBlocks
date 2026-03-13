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

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict

import numpy as np


class Block(ABC):
    """Base class for all discrete-time blocks (Simulink-like).
 
    A block follows two-phase execution per timestep:
    output_update computes y[k] from x[k] and u[k], then state_update
    computes x[k+1] from x[k] and u[k].
 
    Attributes:
        name: Unique identifier for this block instance.
        sample_time: Sampling period in seconds, or None to use the global dt.
        inputs: Input port values, set by the simulator each step.
        outputs: Output port values, written by output_update.
        state: Committed state x[k].
        next_state: Pending state x[k+1], written by state_update.
    """

    direct_feedthrough = True
    """True if outputs depend directly on inputs."""

    is_source = False
    """True if the block produces signals with no inputs."""

    def __init__(self, name: str, sample_time: float | None = None):
        """Initialize a block.
 
        Args:
            name: Unique identifier for this block instance.
            sample_time: Sampling period in seconds, or None to use the
                global simulation dt.
 
        Raises:
            ValueError: If sample_time is provided but not strictly positive.
        """
        self.name = name
 
        if sample_time is not None and sample_time <= 0:
            raise ValueError(f"[{self.name}] sample_time must be > 0.")
        self.sample_time = sample_time
 
        self.inputs: Dict[str, np.ndarray] = {}
        self.outputs: Dict[str, np.ndarray] = {}
        self.state: Dict[str, np.ndarray] = {}
        self.next_state: Dict[str, np.ndarray] = {}
 
        self._effective_sample_time = 0.


    # --------------------------------------------------------------------------
    # Class Methods
    # --------------------------------------------------------------------------
 
    @classmethod
    def adapt_params(cls,
                     params: Dict[str, Any],
                     params_dir: Path | None = None) -> Dict[str, Any]:
        """Adapt parameters from YAML format to constructor format.
 
        Args:
            params: Raw parameter dict loaded from the YAML project file.
            params_dir: Directory of the project file, for resolving relative
                paths. None if not applicable.
 
        Returns:
            Parameter dict ready to be passed to the block constructor.
        """
        return params


    # --------------------------------------------------------------------------
    # Public Methods
    # --------------------------------------------------------------------------

    @property
    def has_state(self) -> bool:
        """True if the block carries internal state."""
        return bool(self.state) or bool(self.next_state)

    @abstractmethod
    def initialize(self, t0: float):
        """Initialize state x[0] and outputs y[0].

        Must populate self.state and self.outputs before the first step.

        Args:
            t0: Initial simulation time in seconds.
        """

    @abstractmethod
    def output_update(self, t: float, dt: float):
        """Compute outputs y[k] from x[k] and inputs u[k].

        Called before state_update each timestep.
        Must write to self.outputs.

        Args:
            t: Current simulation time in seconds.
            dt: Current time step in seconds.
        """

    @abstractmethod
    def state_update(self, t: float, dt: float):
        """Compute next state x[k+1] from x[k] and inputs u[k].

        Must write to self.next_state.

        Args:
            t: Current simulation time in seconds.
            dt: Current time step in seconds.
        """

    def commit_state(self):
        """Copy x[k+1] into x[k] to finalize the timestep.

        Called by the simulator after all blocks have completed state_update.
        """
        for key, value in self.next_state.items():
            self.state[key] = np.copy(value)

    def finalize(self):
        """Clean up resources at the end of the simulation."""


    # --------------------------------------------------------------------------
    # Private Methods
    # --------------------------------------------------------------------------

    @staticmethod
    def _is_scalar_2d(arr: np.ndarray) -> bool:
        """True if arr has shape (1, 1)."""
        return arr.shape == (1, 1)

    def _to_2d_array(self, param_name: str, value, *, dtype=float) -> np.ndarray:
        """Normalize value to a 2D column-oriented array.

        scalar -> (1,1), 1D (n,) -> (n,1), 2D -> preserved, ndim>2 -> error.

        Args:
            param_name: Name of the parameter, used in error messages.
            value: Input value to normalize.
            dtype: Target NumPy dtype.

        Raises:
            ValueError: If value has more than 2 dimensions.
        """
        arr = np.asarray(value, dtype=dtype)

        if arr.ndim == 0:
            return arr.reshape(1, 1)

        if arr.ndim == 1:
            return arr.reshape(-1, 1)

        if arr.ndim == 2:
            if arr.shape[0] == 1 and arr.shape[1] != 1:
                return arr.reshape(-1, 1)
            return arr

        raise ValueError(
            f"[{self.name}] '{param_name}' must be scalar, 1D, or 2D array-like. "
            f"Got ndim={arr.ndim} with shape {arr.shape}."
        )
