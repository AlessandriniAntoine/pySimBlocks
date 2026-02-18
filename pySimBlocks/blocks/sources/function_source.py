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
from typing import Any, Callable, Dict

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
        - Returned value can be scalar, 1D, or 2D (internally normalized to 2D).
        - Output shape is frozen after first successful evaluation.
    """

    def __init__(
        self,
        name: str,
        function: Callable,
        sample_time: float | None = None,
    ):
        super().__init__(name, sample_time)

        if function is None or not callable(function):
            raise TypeError(f"[{self.name}] 'function' must be callable.")

        self._func = function
        self._out_shape: tuple[int, int] | None = None
        self.outputs["out"] = np.zeros((1, 1), dtype=float)

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
        return adapted

    # --------------------------------------------------------------------------
    # Public Methods
    # --------------------------------------------------------------------------
    def initialize(self, t0: float) -> None:
        self._validate_signature()
        self.outputs["out"] = self._call_func(t0, 0.0)

    # ------------------------------------------------------------------
    def output_update(self, t: float, dt: float) -> None:
        self.outputs["out"] = self._call_func(t, dt)

    # --------------------------------------------------------------------------
    # Private Methods
    # --------------------------------------------------------------------------
    def _call_func(self, t: float, dt: float) -> np.ndarray:
        try:
            y = self._func(t, dt)
        except Exception as e:
            raise RuntimeError(f"[{self.name}] function call error: {e}")

        y = self._to_2d_array("out", y, dtype=float)
        if y.ndim != 2:
            raise ValueError(
                f"[{self.name}] function output must be scalar, 1D, or 2D."
            )

        if self._out_shape is None:
            self._out_shape = y.shape
            return y

        if y.shape != self._out_shape:
            raise ValueError(
                f"[{self.name}] output 'out' shape changed: expected "
                f"{self._out_shape}, got {y.shape}."
            )

        return y

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
