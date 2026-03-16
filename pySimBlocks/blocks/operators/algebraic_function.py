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

import importlib.util
import inspect
from pathlib import Path
from typing import Any, Callable, Dict, List

import numpy as np

from pySimBlocks.core.block import Block


class AlgebraicFunction(Block):
    """User-defined algebraic function block.

    Stateless block defined by a user-provided Python callable:

        y = g(t, dt, u1, u2, ...)

    Input and output port names are declared dynamically from ``input_keys``
    and ``output_keys``. All inputs and outputs must be 2D numpy arrays. Input
    and output shapes are frozen per port after the first use.

    Attributes:
        input_keys: Names of the input ports.
        output_keys: Names of the output ports.
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
        """Initialize an AlgebraicFunction block.

        Args:
            name: Unique identifier for this block instance.
            function: User-defined callable with signature
                ``g(t, dt, **inputs) -> dict`` returning a dict mapping each
                key in ``output_keys`` to a 2D numpy array.
            input_keys: Names of the input ports.
            output_keys: Names of the output ports.
            sample_time: Sampling period in seconds, or None to use the global
                simulation dt.

        Raises:
            TypeError: If ``function`` is not callable.
            ValueError: If ``input_keys`` or ``output_keys`` are empty.
        """
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

        self._in_shapes: Dict[str, tuple[int, int] | None] = {k: None for k in self.input_keys}
        self._out_shapes: Dict[str, tuple[int, int] | None] = {k: None for k in self.output_keys}


    # --------------------------------------------------------------------------
    # Class methods
    # --------------------------------------------------------------------------

    @classmethod
    def adapt_params(
        cls,
        params: Dict[str, Any],
        params_dir: Path | None = None,
    ) -> Dict[str, Any]:
        """Load the user function from ``file_path`` and ``function_name`` YAML keys.

        Args:
            params: Raw parameter dict loaded from the YAML project file.
            params_dir: Directory of the project file, for resolving relative
                paths. Must not be None.

        Returns:
            Parameter dict with ``function`` set to the loaded callable and
            ``file_path`` / ``function_name`` keys removed.

        Raises:
            ValueError: If ``params_dir`` is None or required keys are missing.
            FileNotFoundError: If the function file does not exist.
            AttributeError: If the named function is not found in the module.
            TypeError: If the resolved attribute is not callable.
        """
        if params_dir is None:
            raise ValueError("parameters_dir must be provided for AlgebraicFunction adapter.")
        try:
            file_path = params["file_path"]
            func_name = params["function_name"]
        except KeyError as e:
            raise ValueError(
                f"AlgebraicFunction adapter missing parameter: {e}"
            )

        path = Path(file_path).expanduser()
        if not path.is_absolute():
            path = (params_dir / path).resolve()

        if not path.exists():
            raise FileNotFoundError(f"Function file not found: {path}")

        spec = importlib.util.spec_from_file_location(path.stem, path)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)

        try:
            func = getattr(module, func_name)
        except AttributeError:
            raise AttributeError(
                f"Function '{func_name}' not found in {path}"
            )

        if not callable(func):
            raise TypeError(
                f"'{func_name}' in {path} is not callable"
            )

        adapted = dict(params)
        adapted.pop("file_path", None)
        adapted.pop("function_name", None)
        adapted["function"] = func

        return adapted


    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------

    def initialize(self, t0: float) -> None:
        """Validate the function signature and compute initial outputs.

        Args:
            t0: Initial simulation time in seconds.

        Raises:
            ValueError: If the function signature does not match ``input_keys``.
            RuntimeError: If the function does not return the expected output
                keys.
        """
        self._validate_signature()

        out = self._call_func(t0, 0, **self.inputs)
        if not isinstance(out, dict):
            raise RuntimeError(f"[{self.name}] function must return a dict.")

        if set(out.keys()) != set(self.output_keys):
            raise RuntimeError(
                f"[{self.name}] output keys mismatch "
                f"(expected {self.output_keys}, got {list(out.keys())})."
            )
        for k in self.output_keys:
            self.outputs[k] = out[k]

    def output_update(self, t: float, dt: float) -> None:
        """Call the user function and write outputs to the output ports.

        Args:
            t: Current simulation time in seconds.
            dt: Current time step in seconds.

        Raises:
            RuntimeError: If any input is not set or the function fails.
            TypeError: If any input or output is not a numpy array.
            ValueError: If any input or output is not 2D, or if shapes changed.
        """
        kwargs: Dict[str, np.ndarray] = {}
        for k in self.input_keys:
            u = self.inputs[k]
            if u is None:
                raise RuntimeError(f"[{self.name}] input '{k}' is not set.")
            u = np.asarray(u)
            self._check_freeze_shape("input", k, u, self._in_shapes)
            kwargs[k] = u

        out = self._call_func(t, dt, **kwargs)

        for k in self.output_keys:
            y = out[k]
            y = np.asarray(y)
            self._check_freeze_shape("output", k, y, self._out_shapes)
            self.outputs[k] = y

    def state_update(self, t: float, dt: float) -> None:
        """No-op: AlgebraicFunction is a stateless block.

        Args:
            t: Current simulation time in seconds.
            dt: Current time step in seconds.
        """
        return


    # --------------------------------------------------------------------------
    # Private methods
    # --------------------------------------------------------------------------

    def _call_func(self, t: float, dt: float, **kwargs) -> Dict[str, np.ndarray]:
        """Invoke the user function and validate its output dict."""
        try:
            out = self._func(t, dt, **kwargs)
        except Exception as e:
            raise RuntimeError(f"[{self.name}] function call error: {e}\n"
                               f"Must always return a dict with output keys: {self.output_keys}")

        if not isinstance(out, dict):
            raise RuntimeError(f"[{self.name}] function must return a dict.")

        if not set(self.output_keys).issubset(out.keys()):
            raise RuntimeError(
                f"[{self.name}] missing output keys "
                f"(expected {self.output_keys}, got {list(out.keys())})."
            )

        for k in self.output_keys:
            y = out[k]
            if not isinstance(y, np.ndarray):
                raise RuntimeError(f"{self.name}: output '{k}' is not a numpy array")
            if y.ndim > 2:
                raise RuntimeError(f"{self.name}: output '{k}' must be at most 2D (got shape {y.shape})")
        return out

    def _validate_signature(self) -> None:
        """Raise if the function signature does not match (t, dt, *input_keys)."""
        sig = inspect.signature(self._func)
        params = list(sig.parameters.values())

        if len(params) < 2:
            raise ValueError(f"[{self.name}] function must have at least arguments (t, dt).")

        if params[0].name != "t" or params[1].name != "dt":
            raise ValueError(f"[{self.name}] first arguments must be (t, dt).")

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

    def _check_freeze_shape(self, which: str, key: str, arr: np.ndarray, store: Dict[str, tuple[int, int] | None]) -> None:
        """Validate that an array is 2D and freeze its shape on the first call."""
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
