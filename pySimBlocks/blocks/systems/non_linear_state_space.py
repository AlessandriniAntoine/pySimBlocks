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

import importlib.util
import inspect
from pathlib import Path
from typing import Any, Callable, Dict, List

import numpy as np

from pySimBlocks.core.block import Block


class NonLinearStateSpace(Block):
    """User-defined nonlinear state-space block.

    Implements a nonlinear discrete-time system driven by two user-provided
    callables:

        x[k+1] = state_function(t, dt, x, u1, u2, ...)

        y[k]   = output_function(t, dt, x)

    Input and output port names are declared dynamically via ``input_keys``
    and ``output_keys``. All inputs and outputs must be column vectors of
    shape (n, 1).

    Attributes:
        input_keys: Names of the input ports.
        output_keys: Names of the output ports.
    """

    direct_feedthrough = False
    is_source = False

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
        """Initialize a NonLinearStateSpace block.

        Args:
            name: Unique identifier for this block instance.
            state_function: Callable with signature
                ``f(t, dt, x, **inputs) -> np.ndarray`` returning the next
                state as a (n, 1) array.
            output_function: Callable with signature
                ``g(t, dt, x) -> dict`` returning a dict mapping each key
                in ``output_keys`` to a (n, 1) array.
            input_keys: Names of the input ports.
            output_keys: Names of the output ports.
            x0: Initial state as a numpy array of shape (n, 1) or (n,).
            sample_time: Sampling period in seconds, or None to use the
                global simulation dt.

        Raises:
            TypeError: If x0 is not a numpy array.
            ValueError: If x0 does not have shape (n, 1) or (n,).
        """
        super().__init__(name=name, sample_time=sample_time)

        self._state_func = state_function
        self._output_func = output_function
        self.input_keys = list(input_keys)
        self.output_keys = list(output_keys)

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


    # --------------------------------------------------------------------------
    # Class methods
    # --------------------------------------------------------------------------

    @classmethod
    def adapt_params(cls,
                     params: Dict[str, Any],
                     params_dir: Path | None = None) -> Dict[str, Any]:
        """Load state and output callables from ``file_path`` YAML keys.

        Args:
            params: Raw parameter dict loaded from the YAML project file.
            params_dir: Directory of the project file, for resolving relative
                paths. Must not be None.

        Returns:
            Parameter dict with ``state_function`` and ``output_function``
            set to the loaded callables, and ``file_path``,
            ``state_function_name``, ``output_function_name`` keys removed.

        Raises:
            ValueError: If ``params_dir`` is None or if required keys are
                missing from ``params``.
            FileNotFoundError: If the function file does not exist.
            AttributeError: If a named function is not found in the module.
            TypeError: If a resolved attribute is not callable.
        """
        if params_dir is None:
            raise ValueError("parameters_dir must be provided for AlgebraicFunction adapter.")
        try:
            file_path = params["file_path"]
            state_func_name = params["state_function_name"]
            output_func_name = params["output_function_name"]
        except KeyError as e:
            raise ValueError(
                f"NonLinearStateSpace adapter missing parameter: {e}"
            )

        path = Path(file_path).expanduser()
        if not path.is_absolute():
            path = (params_dir / path).resolve()

        if not path.exists():
            raise FileNotFoundError(
                f"NonLinearStateSpace function file not found: {path}"
            )

        spec = importlib.util.spec_from_file_location(path.stem, path)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)

        try:
            state_func: Callable = getattr(module, state_func_name)
        except AttributeError:
            raise AttributeError(
                f"State function '{state_func_name}' not found in {path}"
            )

        try:
            output_func: Callable = getattr(module, output_func_name)
        except AttributeError:
            raise AttributeError(
                f"Output function '{output_func_name}' not found in {path}"
            )

        if not callable(state_func):
            raise TypeError(
                f"'{state_func_name}' in {path} is not callable"
            )

        if not callable(output_func):
            raise TypeError(
                f"'{output_func_name}' in {path} is not callable"
            )

        adapted = dict(params)
        adapted.pop("file_path", None)
        adapted.pop("state_function_name", None)
        adapted.pop("output_function_name", None)
        adapted["state_function"] = state_func
        adapted["output_function"] = output_func

        return adapted


    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------

    def initialize(self, t0: float) -> None:
        """Validate function signatures and declare input/output ports.

        Args:
            t0: Initial simulation time in seconds.
        """
        self._validate_signature()

        for k in self.input_keys:
            self.inputs[k] = None

        for k in self.output_keys:
            self.outputs[k] = None

    def output_update(self, t: float, dt: float) -> None:
        """Call the output function and write results to the output ports.

        Args:
            t: Current simulation time in seconds.
            dt: Current time step in seconds.
        """
        assert self._output_func is not None

        x = self.state["x"]
        out = self._call_output_func(t, dt, x=x)

        for k in self.output_keys:
            self.outputs[k] = out[k]

    def state_update(self, t: float, dt: float) -> None:
        """Call the state function and store the next state.

        Args:
            t: Current simulation time in seconds.
            dt: Current time step in seconds.

        Raises:
            TypeError: If any input value is not a numpy array.
            ValueError: If any input does not have shape (n, 1).
        """
        assert self._output_func is not None

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

        x = self.state["x"]
        out = self._state_func(t, dt, x=x, **kwargs)
        self.next_state["x"] = out


    # --------------------------------------------------------------------------
    # Private methods
    # --------------------------------------------------------------------------

    def _call_state_func(self, t, dt, x, **kwargs) -> np.ndarray:
        """Invoke the state function and validate its (n,1) array output."""
        try:
            out = self._state_func(t, dt, x, **kwargs)
        except Exception as e:
            raise RuntimeError(f"{self.name}: state function call error: {e}\n"
                               f"Must always return the next state as a column vector array.")

        if not isinstance(out, np.ndarray):
            raise RuntimeError(f"{self.name}: state function must return a numpy array")
        if out.ndim != 2 or out.shape[1] != 1:
            raise RuntimeError(f"{self.name}: state function must return an array of shape (n,1)")

        return out

    def _call_output_func(self, t, dt, x) -> Dict[str, np.ndarray]:
        """Invoke the output function and validate its dict output."""
        try:
            out = self._output_func(t, dt, x)
        except Exception as e:
            raise RuntimeError(f"{self.name}: output function call error: {e}\n"
                               f"Must always return a dict with output keys: {self.output_keys}")

        if not isinstance(out, dict):
            raise RuntimeError(f"{self.name}: output function must return a dict")
        if set(out.keys()) != set(self.output_keys):
            raise RuntimeError(
                f"{self.name}: output keys mismatch "
                f"(expected {self.output_keys}, got {list(out.keys())})"
            )
        for k in self.output_keys:
            y = out[k]
            if not isinstance(y, np.ndarray):
                raise RuntimeError(f"{self.name}: output '{k}' is not a numpy array")
            if y.ndim != 2 or y.shape[1] != 1:
                raise RuntimeError(f"{self.name}: output '{k}' must have shape (n,1)")

        return out

    def _validate_signature(self) -> None:
        """Raise if state or output functions do not have the expected signature (t, dt, x, ...)."""
        assert self._state_func is not None
        assert self._output_func is not None

        for f in [self._state_func, self._output_func]:
            sig = inspect.signature(f)
            params = list(sig.parameters.values())

            if len(params) < 3:
                raise ValueError(
                    f"{self.name}: function must have at least arguments (t, dt, x)"
                )

            if params[0].name != "t" or params[1].name != "dt" or params[2].name != "x":
                raise ValueError(
                    f"{self.name}: first arguments must be (t, dt, x)"
                )

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
