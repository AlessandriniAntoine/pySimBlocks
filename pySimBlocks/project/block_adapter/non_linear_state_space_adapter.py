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

import importlib.util
from pathlib import Path
from typing import Callable


def non_linear_state_space_adapter(
    params: dict,
    parameters_dir: Path,
) -> dict:
    """
    Adapt declarative parameters of NonLinearStateSpace
    into executable parameters.

    Expected input:
        {
            "file_path": "...",
            "state_function_name": "...",
            "output_function_name": "...",
            "input_keys": [...],
            "output_keys": [...],
            "sample_time": ...
        }

    Output:
        {
            "state_function": callable,
            "output_function": callable,
            "input_keys": [...],
            "output_keys": [...],
            "sample_time": ...
        }
    """

    # --------------------------------------------------
    # 1. Validate required fields
    # --------------------------------------------------
    try:
        file_path = params["file_path"]
        state_func_name = params["state_function_name"]
        output_func_name = params["output_function_name"]
    except KeyError as e:
        raise ValueError(
            f"NonLinearStateSpace adapter missing parameter: {e}"
        )

    # --------------------------------------------------
    # 2. Resolve file path (relative to parameters.yaml)
    # --------------------------------------------------
    path = Path(file_path)
    if not path.is_absolute():
        path = (parameters_dir / path).resolve()

    if not path.exists():
        raise FileNotFoundError(
            f"NonLinearStateSpace function file not found: {path}"
        )

    # --------------------------------------------------
    # 3. Load module
    # --------------------------------------------------
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    # --------------------------------------------------
    # 4. Extract functions
    # --------------------------------------------------
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

    # --------------------------------------------------
    # 5. Build adapted parameter dict
    # --------------------------------------------------
    adapted = dict(params)

    # remove declarative-only keys
    adapted.pop("file_path", None)
    adapted.pop("state_function_name", None)
    adapted.pop("output_function_name", None)

    # inject executable callables
    adapted["state_function"] = state_func
    adapted["output_function"] = output_func

    return adapted

