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
from pySimBlocks.core.config import ModelConfig, SimulationConfig

# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def _load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Parameters file not found: {path}")

    with path.open("r") as f:
        data = yaml.safe_load(f) or {}

    if not isinstance(data, dict):
        raise ValueError("parameters.yaml must define a YAML mapping")

    return data

def convert_to_str(raw: dict) -> dict:
    def _convert(v):
        if v is None:
            return None
        return str(v)

    if "simulation" in raw:
        raw["simulation"] = {k: _convert(v) for k, v in raw["simulation"].items()}

    if "blocks" in raw:
        raw["blocks"] = {
            b: {k: _convert(v) for k, v in params.items()}
            for b, params in raw["blocks"].items()
        }

    return raw



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
                "but no 'external' module is defined"
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
    parameters_yaml: str | Path,
    parameters_dir: Path | None = None,
) -> Tuple[SimulationConfig, ModelConfig]:
    """
    Load the configuration required to run a simulation.
    If a plot config is needed, use: load_project_config

    This function parses:
      - simulation configuration,
      - model numerical parameters,

    Parameters:
        parameters_yaml: path to parameters.yaml

    Returns:
        (SimulationConfig, ModelConfig)
    """
    parameters_yaml = Path(parameters_yaml)
    raw = _load_yaml(parameters_yaml)
    raw = convert_to_str(raw)

    # ------------------------------------------------------------
    # External module handling
    # ------------------------------------------------------------
    external_module = None
    scope = {}

    if "external" in raw:
        external = raw["external"]
        if not isinstance(external, str):
            raise ValueError("'external' must be a path to a Python file")

        external_path = parameters_yaml.parent / external
        external_module, scope = _load_external_module(external_path)
    else:
        _check_no_external_refs(raw)

    # ------------------------------------------------------------
    # Resolve external references
    # ------------------------------------------------------------
    resolved = (
        _resolve_external_refs(raw, external_module)
        if external_module is not None
        else raw
    )

    # ------------------------------------------------------------
    # SimulationConfig
    # ------------------------------------------------------------
    sim_data = resolved.get("simulation", {})
    if not sim_data:
        raise ValueError("Missing 'simulation' section in parameters.yaml")

    required = {"dt", "T"}
    missing = required - sim_data.keys()
    if missing:
        raise ValueError(
            f"Missing required simulation parameters: {sorted(missing)}"
        )

    sim_data = eval_recursive(sim_data, scope)

    sim_cfg = SimulationConfig(
        dt=sim_data["dt"],
        T=sim_data["T"],
        t0=sim_data.get("t0", 0.0),
        solver=sim_data.get("solver", "fixed"),
        logging=resolved.get("logging", []),
        clock=sim_data.get("clock", "internal")
    )

    sim_cfg.validate()

    # ------------------------------------------------------------
    # ModelConfig
    # ------------------------------------------------------------
    blocks_data = resolved.get("blocks", {})
    blocks_data = eval_recursive(blocks_data, scope)
    if not isinstance(blocks_data, dict):
        raise ValueError("'blocks' section must be a mapping")

    if parameters_dir is None:
        parameters_dir = parameters_yaml.parent.resolve()

    model_cfg = ModelConfig(
        blocks=blocks_data,
        parameters_dir=parameters_dir,
    )

    return sim_cfg, model_cfg
