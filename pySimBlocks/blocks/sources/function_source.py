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

from pySimBlocks.core.block_source import BlockSource


class FunctionSource(BlockSource):
    """
    User-defined source block with no inputs.

    Summary:
        Computes:
            y = f(t, dt)

    Notes:
        - The function must accept exactly (t, dt).
        - Function must return a dict with keys matching output_keys.
        - Each output value can be scalar, 1D, or 2D (internally normalized to 2D).
        - Output shape is frozen independently for each output key.
    """

    def __init__(
        self,
        name: str,
        function: Callable,
        output_keys: List[str] | None = None,
        sample_time: float | None = None,
    ):
        super().__init__(name, sample_time)

        if function is None or not callable(function):
            raise TypeError(f"[{self.name}] 'function' must be callable.")

        self._func = function
        self.output_keys = ["out"] if output_keys is None else list(output_keys)
        if len(self.output_keys) == 0:
            raise ValueError(f"[{self.name}] output_keys cannot be empty.")

        self.outputs: Dict[str, np.ndarray | None] = {k: None for k in self.output_keys}
        self._out_shapes: Dict[str, tuple[int, int] | None] = {
            k: None for k in self.output_keys
        }

    # --------------------------------------------------------------------------
    # Class Methods
    # --------------------------------------------------------------------------
    @classmethod
    def adapt_params(
        cls,
        params: Dict[str, Any],
        params_dir: Path | None = None,
    ) -> Dict[str, Any]:
        """
        Adapt YAML parameters by loading a callable from (file_path, function_name).
        """
        adapted = dict(params)

        if "function" in adapted:
            return adapted

        has_file = "file_path" in adapted
        has_name = "function_name" in adapted
        if not has_file and not has_name:
            return adapted
        if not has_file or not has_name:
            raise ValueError(
                "FunctionSource adapter requires both 'file_path' and 'function_name'."
            )

        path = Path(adapted["file_path"])
        if not path.is_absolute() and params_dir is not None:
            path = (params_dir / path).resolve()

        if not path.exists():
            raise FileNotFoundError(f"Function file not found: {path}")

        spec = importlib.util.spec_from_file_location(path.stem, path)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)

        func_name = adapted["function_name"]
        try:
            func = getattr(module, func_name)
        except AttributeError:
            raise AttributeError(f"Function '{func_name}' not found in {path}")

        if not callable(func):
            raise TypeError(f"'{func_name}' in {path} is not callable")

        adapted.pop("file_path", None)
        adapted.pop("function_name", None)
        adapted["function"] = func
        if "output_keys" not in adapted:
            adapted["output_keys"] = ["out"]
        return adapted

    # --------------------------------------------------------------------------
    # Public Methods
    # --------------------------------------------------------------------------
    def initialize(self, t0: float) -> None:
        self._validate_signature()
        out = self._call_func(t0, 0.0)
        for key in self.output_keys:
            self.outputs[key] = out[key]

    # ------------------------------------------------------------------
    def output_update(self, t: float, dt: float) -> None:
        out = self._call_func(t, dt)
        for key in self.output_keys:
            self.outputs[key] = out[key]

    # --------------------------------------------------------------------------
    # Private Methods
    # --------------------------------------------------------------------------
    def _call_func(self, t: float, dt: float) -> Dict[str, np.ndarray]:
        try:
            out = self._func(t, dt)
        except Exception as e:
            raise RuntimeError(f"[{self.name}] function call error: {e}")

        if not isinstance(out, dict):
            raise RuntimeError(
                f"[{self.name}] function must return a dict with output keys: "
                f"{self.output_keys}."
            )

        if set(out.keys()) != set(self.output_keys):
            raise RuntimeError(
                f"[{self.name}] output keys mismatch "
                f"(expected {self.output_keys}, got {list(out.keys())})."
            )

        normalized: Dict[str, np.ndarray] = {}
        for key in self.output_keys:
            y = self._to_2d_array(key, out[key], dtype=float)
            if y.ndim != 2:
                raise ValueError(
                    f"[{self.name}] output '{key}' must be scalar, 1D, or 2D."
                )

            if self._out_shapes[key] is None:
                self._out_shapes[key] = y.shape
            elif y.shape != self._out_shapes[key]:
                raise ValueError(
                    f"[{self.name}] output '{key}' shape changed: expected "
                    f"{self._out_shapes[key]}, got {y.shape}."
                )
            normalized[key] = y

        return normalized

    # ------------------------------------------------------------------
    def _validate_signature(self) -> None:
        sig = inspect.signature(self._func)
        params = list(sig.parameters.values())

        if len(params) != 2:
            raise ValueError(
                f"[{self.name}] function must have exactly arguments (t, dt)."
            )
        if params[0].name != "t" or params[1].name != "dt":
            raise ValueError(
                f"[{self.name}] function arguments must be exactly (t, dt)."
            )

        for p in params:
            if p.kind not in (inspect.Parameter.POSITIONAL_OR_KEYWORD,):
                raise ValueError(f"[{self.name}] *args and **kwargs are not allowed.")
            if p.default is not inspect.Parameter.empty:
                raise ValueError(
                    f"[{self.name}] default values are not allowed in function signature."
                )
