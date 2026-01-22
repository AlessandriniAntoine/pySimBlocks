# ******************************************************************************
#                                 pySimBlocks                                 
#                Copyright (c) 2026 The pySimBlocks Authors               
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

import inspect
from typing import Callable, List, Dict

import numpy as np

from pySimBlocks.core.block import Block


class NonLinearStateSpace(Block):
    """
    User-defined algebraic function block.

    Summary:
        Stateless block defined by a user-provided Python function:
            x+ = f(t, dt, x, u1, u2, ...)
            y = g(t, dt, x)

    Parameters:
        state_function : callable
            Function to compute next state.
        output_function_name : callable
            Function to compute outputs.
        input_keys : list[str]
            Names of input ports.
        output_keys : list[str]
            Names of output ports.
        sample_time : float, optional
            Block execution period.

    I/O:
        Inputs:
            Defined dynamically by input_keys.
        Outputs:
            Defined dynamically by output_keys.

    Notes:
        - This block is stateless.
        - Ports are fully declarative (V1).
        - The function must return a dict with exactly output_keys.
        - All inputs and outputs must be numpy arrays of shape (n,1).
    """

    direct_feedthrough = False
    is_source = False

    # ------------------------------------------------------------------
    def __init__(
        self,
        name: str,
        state_function: Callable,
        output_function: Callable,
        input_keys: List[str],
        output_keys: List[str],
        x0: np.ndarray,
        sample_time: float | None = None,
    ):
        super().__init__(name=name, sample_time=sample_time)

        # ---- parameters
        self._state_func = state_function
        self._output_func = output_function
        self.input_keys = list(input_keys)
        self.output_keys = list(output_keys)

        # ---- initial state
        if not isinstance(x0, np.ndarray):
            raise TypeError(
                f"{self.name}: x0 must be a numpy array"
            )
        if x0.ndim == 1:
            x0 = x0.reshape(-1, 1)
        elif x0.ndim != 2 or x0.shape[1] != 1:
            raise ValueError(
                f"{self.name}: x0 must have shape (n,1) or (n,)"
            )
        self.state["x"] = x0.copy()
        self.next_state["x"] = x0.copy()

    # ------------------------------------------------------------------
    def initialize(self, t0: float):
        """
        Load the user function and validate its signature.
        """
        self._validate_signature()

        # ---- declare ports
        for k in self.input_keys:
            self.inputs[k] = None

        for k in self.output_keys:
            self.outputs[k] = None

    # ------------------------------------------------------------------
    def _validate_signature(self):
        """
        Validate function signature against input_keys.
        """
        assert self._state_func is not None
        assert self._output_func is not None

        for f in [self._state_func, self._output_func]:
            sig = inspect.signature(f)
            params = list(sig.parameters.values())

            # ---- minimum signature: (t, dt, ...)
            if len(params) < 3:
                raise ValueError(
                    f"{self.name}: function must have at least arguments (t, dt, x)"
                )

            if params[0].name != "t" or params[1].name != "dt" or params[2].name != "x":
                raise ValueError(
                    f"{self.name}: first arguments must be (t, dt, x)"
                )

            # ---- no *args / **kwargs / defaults
            for p in params:
                if p.kind not in (
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                ):
                    raise ValueError(
                        f"{self.name}: *args and **kwargs are not allowed"
                    )
                if p.default is not inspect.Parameter.empty:
                    raise ValueError(
                        f"{self.name}: default arguments are not allowed"
                    )

    # ------------------------------------------------------------------
    def output_update(self, t: float, dt: float):
        """
        Compute outputs from current inputs.
        """
        assert self._output_func is not None

        # ---- call function
        x = self.state["x"]
        out = self._output_func(t, dt, x=x)

        if not isinstance(out, dict):
            raise RuntimeError(
                f"{self.name}: function must return a dict"
            )

        if set(out.keys()) != set(self.output_keys):
            raise RuntimeError(
                f"{self.name}: output keys mismatch "
                f"(expected {self.output_keys}, got {list(out.keys())})"
            )

        # ---- assign outputs
        for k in self.output_keys:
            y = out[k]
            if not isinstance(y, np.ndarray):
                raise TypeError(
                    f"{self.name}: output '{k}' is not a numpy array"
                )
            if y.ndim != 2 or y.shape[1] != 1:
                raise ValueError(
                    f"{self.name}: output '{k}' must have shape (n,1)"
                )

            self.outputs[k] = y

    def state_update(self, t: float, dt: float):
        """
        Compute next state from current inputs.
        """
        assert self._output_func is not None

        # ---- collect inputs
        kwargs: Dict[str, np.ndarray] = {}
        for k in self.input_keys:
            u = self.inputs[k]
            if not isinstance(u, np.ndarray):
                raise TypeError(
                    f"{self.name}: input '{k}' is not a numpy array"
                )
            if u.ndim != 2 or u.shape[1] != 1:
                raise ValueError(
                    f"{self.name}: input '{k}' must have shape (n,1)"
                )
            kwargs[k] = u

        # ---- call function
        x = self.state["x"]
        out = self._state_func(t, dt, x=x, **kwargs)
        self.next_state["x"] = out
