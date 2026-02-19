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
from pathlib import Path
from typing import Dict, Any, Tuple
import yaml
import numpy as np
import re
from pySimBlocks.core.config import SimulationConfig

# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def _load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Project file not found: {path}")

    with path.open("r") as f:
        data = yaml.safe_load(f) or {}

    if not isinstance(data, dict):
        raise ValueError("project.yaml must define a YAML mapping")

    return data



############################################################
# External variables
############################################################
def _load_external_module(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"External parameters module not found: {path}")

    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)

    assert spec.loader is not None
    spec.loader.exec_module(module)

    return module, module.__dict__


_EXTERNAL_REF_PATTERN = re.compile(r"#([A-Za-z_][A-Za-z0-9_]*)")
def extract_external_refs(expr: str) -> set[str]:
    """
    Extract all external references (#var) from an expression string.
    """
    return set(_EXTERNAL_REF_PATTERN.findall(expr))


def _resolve_external_refs(obj: Any, external_module) -> Any:
    """
    Recursively validate #var references using the external module.
    Does NOT replace anything.
    """
    if isinstance(obj, str):
        refs = extract_external_refs(obj)
        for name in refs:
            if not hasattr(external_module, name):
                raise KeyError(
                    f"External parameter '{name}' not found "
                    f"in module '{external_module.__file__}'"
                )
        return obj

    if isinstance(obj, list):
        return [_resolve_external_refs(v, external_module) for v in obj]

    if isinstance(obj, dict):
        return {
            k: _resolve_external_refs(v, external_module)
            for k, v in obj.items()
        }

    return obj

def _check_no_external_refs(obj):
    if isinstance(obj, str):
        refs = extract_external_refs(obj)
        if refs:
            raise ValueError(
                f"Found external references {sorted(refs)} "
                "but no external module is defined"
            )

    elif isinstance(obj, list):
        for v in obj:
            _check_no_external_refs(v)

    elif isinstance(obj, dict):
        for v in obj.values():
            _check_no_external_refs(v)



############################################################
# EVAL
############################################################
def eval_value(value: Any, scope: dict):
    """
    Try to evaluate ANY value as a Python expression.

    Rules:
    - value is first converted to string
    - '#' is stripped (used as internal keyword)
    - lists are wrapped into np.array
    - eval is attempted with a restricted namespace
    - if eval fails → return original value
    """

    try:
        expr = str(value)
        expr = expr.replace("#", "")
        expr = re.sub(r'(?<!np\.array)\[', 'np.array([', expr)
        expr = re.sub(r'\]', '])', expr)
        return eval(expr, {"np": np}, scope)
    except Exception:
        return value


def eval_recursive(obj: Any, scope: dict):
    if isinstance(obj, dict):
        return {k: eval_recursive(v, scope) for k, v in obj.items()}

    if isinstance(obj, list):
        return [eval_recursive(v, scope) for v in obj]

    return eval_value(obj, scope)

# ---------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------
def load_simulation_config(
    project_yaml: str | Path,
) -> Tuple[SimulationConfig, Dict[str, Any], Path]:
    """
    Load simulation and diagram configuration from unified project.yaml.

    Returns:
        (SimulationConfig, model_dict, params_dir)
    """
    from pySimBlocks.project.load_project_config import load_project_config

    sim_cfg, model_dict, _plot_cfg, _project_name, params_dir = load_project_config(
        project_yaml
    )
    return sim_cfg, model_dict, params_dir
