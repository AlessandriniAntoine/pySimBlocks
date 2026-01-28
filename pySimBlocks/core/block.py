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

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict

import numpy as np


class Block(ABC):
    """
    Base class for all discrete-time blocks (Simulink-like).

    A block follows two-phase execution:

    1) output_update(t, dt):
           Computes outputs y[k] from:
                - current state x[k]
                - current inputs u[k]

    2) state_update(t, dt):
           Computes next state x[k+1] from:
                - current state x[k]
                - current inputs u[k]
    """

    direct_feedthrough = True
    is_source = False

    def __init__(self, name: str, sample_time: float | None = None):
        self.name = name

        if sample_time is not None and sample_time <= 0:
            raise ValueError(f"[{self.name}] sample_time must be > 0.")
        self.sample_time = sample_time

        # Dict[str -> np.ndarray]
        self.inputs = {}    # ports set by the simulator
        self.outputs = {}   # ports produced at each step

        # Internal states:
        # state: x[k]       (committed state)
        # next_state: x[k+1] (to commit at end of step)
        self.state = {}
        self.next_state = {}

        self._effective_sample_time = 0.
        
        
    # --------------------------------------------------------------------------
    # Class Methods
    # --------------------------------------------------------------------------
    @classmethod
    def adapt_params(cls, 
                     params: Dict[str, Any], 
                     params_dir: Path | None = None) -> Dict[str, Any]:
        """
        Adapt parameters from yaml format to class constructor format.
        By default, does nothing.
        """
        return params
        
        
    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------
    @property
    def has_state(self) -> bool:
        """Specify if block is stateful."""
        return bool(self.state) or bool(self.next_state)

    # ------------------------------------------------------------------
    @abstractmethod
    def initialize(self, t0: float):
        """
        Initialize internal state x[0] and outputs y[0].
        Must fill:
            - self.state[...]        (initial state)
            - self.outputs[...]      (initial outputs)
        """

    # ------------------------------------------------------------------
    @abstractmethod
    def output_update(self, t: float, dt: float):
        """
        Compute outputs y[k] from x[k] and inputs u[k].
        Called before state_update.
        Must write to self.outputs[...].
        """

    # ------------------------------------------------------------------
    @abstractmethod
    def state_update(self, t: float, dt: float):
        """
        Compute next state x[k+1] from x[k] and inputs u[k].
        Must write to self.next_state[...].
        """

    # ------------------------------------------------------------------
    def commit_state(self):
        """
        Finalize the step by copying x[k+1] into x[k].
        Called by the simulator after all blocks completed state_update().
        """
        for key, value in self.next_state.items():
            self.state[key] = np.copy(value)

    # ------------------------------------------------------------------
    def finalize(self):
        """
        Optional cleanup method called at the end of the simulation.
        """
        
        
    # --------------------------------------------------------------------------
    # Private methods
    # --------------------------------------------------------------------------
    @staticmethod
    def _is_scalar_2d(arr: np.ndarray) -> bool:
        return arr.shape == (1, 1)

    # ------------------------------------------------------------------
    def _to_2d_array(self, param_name: str, value, *, dtype=float) -> np.ndarray:
        """
        Normalize into a 2D NumPy array.

        Rules:
            - scalar -> (1,1)
            - 1D -> (n,1) (column vector convention)
            - 2D -> preserved as-is (m,n)
            - ndim > 2 -> rejected
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
