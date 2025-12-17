import importlib.util
from pathlib import Path
from typing import Dict, Any, Tuple
import yaml
from fractions import Fraction
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


def _load_external_module(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"External parameters module not found: {path}")

    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)

    assert spec.loader is not None
    spec.loader.exec_module(module)

    return module


def _resolve_external_refs(obj: Any, external_module) -> Any:
    """
    Recursively resolve @xxx references using the external module.
    """
    if isinstance(obj, str) and obj.startswith("@"):
        name = obj[1:]
        if not hasattr(external_module, name):
            raise KeyError(
                f"External parameter '{name}' not found "
                f"in module '{external_module.__file__}'"
            )
        return getattr(external_module, name)

    if isinstance(obj, list):
        return [_resolve_external_refs(v, external_module) for v in obj]

    if isinstance(obj, dict):
        return {
            k: _resolve_external_refs(v, external_module)
            for k, v in obj.items()
        }

    return obj


def _check_no_external_refs(obj):
    if isinstance(obj, str) and obj.startswith("@"):
        raise ValueError(
            "Found external reference '@...' but no 'external' module is defined"
        )
    if isinstance(obj, list):
        for v in obj:
            _check_no_external_refs(v)
    if isinstance(obj, dict):
        for v in obj.values():
            _check_no_external_refs(v)


def parse_numeric(value):
    """
    Parse numeric values from YAML.
    Supports:
      - int
      - float
      - fractions as strings: "a/b"
    Preserves integers when possible.
    """
    # Already numeric → keep type
    if isinstance(value, int):
        return value

    if isinstance(value, float):
        return value

    if isinstance(value, str):
        value = value.strip()

        # Fraction
        if "/" in value:
            try:
                return float(Fraction(value))
            except Exception:
                raise ValueError(f"Invalid fraction expression: '{value}'")

        # Integer string
        if value.isdigit() or (value.startswith("-") and value[1:].isdigit()):
            return int(value)

        # Float string
        try:
            return float(value)
        except ValueError:
            raise ValueError(f"Invalid numeric value: '{value}'")

    raise TypeError(f"Unsupported numeric type: {type(value)}")



def parse_numeric_recursive(obj):
    """
    Recursively parse numeric values.
    Only parses values that are numeric-like.
    Leaves strings untouched unless they are valid numeric expressions.
    """
    if isinstance(obj, dict):
        return {k: parse_numeric_recursive(v) for k, v in obj.items()}

    if isinstance(obj, list):
        return [parse_numeric_recursive(v) for v in obj]

    # Only parse numeric-like strings
    if isinstance(obj, str):
        try:
            return parse_numeric(obj)
        except (ValueError, TypeError):
            return obj  # keep string as-is

    return obj


# ---------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------
def load_simulation_config(
    parameters_yaml: str | Path
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

    # ------------------------------------------------------------
    # External module handling
    # ------------------------------------------------------------
    external_module = None

    if "external" in raw:
        external = raw["external"]
        if not isinstance(external, str):
            raise ValueError("'external' must be a path to a Python file")

        external_path = parameters_yaml.parent / external
        external_module = _load_external_module(external_path)
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

    sim_data = parse_numeric_recursive(sim_data)

    sim_cfg = SimulationConfig(
        dt=sim_data["dt"],
        T=sim_data["T"],
        t0=sim_data.get("t0", 0.0),
        solver=sim_data.get("solver", "fixed"),
        logging=resolved.get("logging", []),
    )

    sim_cfg.validate()

    # ------------------------------------------------------------
    # ModelConfig
    # ------------------------------------------------------------
    blocks_data = resolved.get("blocks", {})
    blocks_data = parse_numeric_recursive(blocks_data)
    if not isinstance(blocks_data, dict):
        raise ValueError("'blocks' section must be a mapping")

    model_cfg = ModelConfig(blocks=blocks_data)

    return sim_cfg, model_cfg
