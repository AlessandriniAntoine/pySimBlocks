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


class AlgebraicFunction(Block):
    """
    User-defined algebraic function block.

    Summary:
        Stateless block defined by a user-provided Python function:
            y = g(t, dt, u1, u2, ...)

    Parameters:
        function : callable
            User-defined function.
        input_keys : list[str]
            Names of input ports.
        output_keys : list[str]
            Names of output ports.
        sample_time : float, optional
            Block execution period.

    Notes:
        - Stateless.
        - Function must return a dict with exactly output_keys.
        - Inputs/outputs must be 2D numpy arrays (matrices allowed).
        - Input/output shapes are frozen per port after first resolution.
    """

    direct_feedthrough = True
    is_source = False

    def __init__(
        self,
        name: str,
        function: Callable,
        input_keys: List[str],
        output_keys: List[str],
        sample_time: float | None = None,
    ):
        super().__init__(name=name, sample_time=sample_time)

        if function is None or not callable(function):
            raise TypeError(f"[{self.name}] 'function' must be callable.")

        self._func = function
        self.input_keys = list(input_keys)
        self.output_keys = list(output_keys)

        if len(self.input_keys) == 0:
            raise ValueError(f"[{self.name}] input_keys cannot be empty.")
        if len(self.output_keys) == 0:
            raise ValueError(f"[{self.name}] output_keys cannot be empty.")

        self.inputs: Dict[str, np.ndarray | None] = {k: None for k in self.input_keys}
        self.outputs: Dict[str, np.ndarray | None] = {k: None for k in self.output_keys}

        # Shape freeze per port
        self._in_shapes: Dict[str, tuple[int, int] | None] = {k: None for k in self.input_keys}
        self._out_shapes: Dict[str, tuple[int, int] | None] = {k: None for k in self.output_keys}

    # ------------------------------------------------------------------
    def initialize(self, t0: float):
        self._validate_signature()

        out = self._func(t0, 0, **self.inputs)
        if not isinstance(out, dict):
            raise RuntimeError(f"[{self.name}] function must return a dict.")

        if set(out.keys()) != set(self.output_keys):
            raise RuntimeError(
                f"[{self.name}] output keys mismatch "
                f"(expected {self.output_keys}, got {list(out.keys())})."
            )
        for k in self.output_keys:
            self.outputs[k] = out[k]

    # ------------------------------------------------------------------
    def _validate_signature(self) -> None:
        sig = inspect.signature(self._func)
        params = list(sig.parameters.values())

        if len(params) < 2:
            raise ValueError(f"[{self.name}] function must have at least arguments (t, dt).")

        if params[0].name != "t" or params[1].name != "dt":
            raise ValueError(f"[{self.name}] first arguments must be (t, dt).")

        # no *args / **kwargs / defaults
        for p in params:
            if p.kind not in (inspect.Parameter.POSITIONAL_OR_KEYWORD,):
                raise ValueError(f"[{self.name}] *args and **kwargs are not allowed.")
            
        declared = [p.name for p in params[2:]]
        if set(declared) != set(self.input_keys):
            raise ValueError(
                f"[{self.name}] function arguments mismatch.\n"
                f"Expected inputs: {self.input_keys}\n"
                f"Function declares: {declared}"
            )

    # ------------------------------------------------------------------
    def _check_freeze_shape(self, which: str, key: str, arr: np.ndarray, store: Dict[str, tuple[int, int] | None]) -> None:
        if not isinstance(arr, np.ndarray):
            raise TypeError(f"[{self.name}] {which} '{key}' is not a numpy array.")
        if arr.ndim != 2:
            raise ValueError(f"[{self.name}] {which} '{key}' must be a 2D array. Got shape {arr.shape}.")

        if store[key] is None:
            store[key] = arr.shape
            return

        if arr.shape != store[key]:
            raise ValueError(
                f"[{self.name}] {which} '{key}' shape changed: expected {store[key]}, got {arr.shape}."
            )

    # ------------------------------------------------------------------
    def output_update(self, t: float, dt: float):
        # collect inputs
        kwargs: Dict[str, np.ndarray] = {}
        for k in self.input_keys:
            u = self.inputs[k]
            if u is None:
                raise RuntimeError(f"[{self.name}] input '{k}' is not set.")
            u = np.asarray(u)  # allow array-like injection, but freeze as ndarray 2D
            self._check_freeze_shape("input", k, u, self._in_shapes)
            kwargs[k] = u

        # call function
        out = self._func(t, dt, **kwargs)

        if not isinstance(out, dict):
            raise RuntimeError(f"[{self.name}] function must return a dict.")

        # Ici on verifie juste que les clés de sorties sont dans la sortie (mais certaines peuvent etre non utilisées)
        if not set(self.output_keys).issubset(out.keys()):
            raise RuntimeError(
                f"[{self.name}] missing output keys "
                f"(expected {self.output_keys}, got {list(out.keys())})."
            )

        # assign outputs
        for k in self.output_keys:
            y = out[k]
            y = np.asarray(y)
            self._check_freeze_shape("output", k, y, self._out_shapes)
            self.outputs[k] = y

    # ------------------------------------------------------------------
    def state_update(self, t: float, dt: float):
        return  # stateless
