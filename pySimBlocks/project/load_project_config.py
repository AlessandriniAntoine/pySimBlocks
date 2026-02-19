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

from pathlib import Path
from typing import Any, Dict, Tuple

from pySimBlocks.core.config import PlotConfig, SimulationConfig
from pySimBlocks.project.load_simulation_config import (
    _check_no_external_refs,
    _load_external_module,
    _load_yaml,
    _resolve_external_refs,
    eval_recursive,
)


def _validate_schema_version(raw: Dict[str, Any]) -> None:
    schema_version = raw.get("schema_version", None)
    if schema_version != 1:
        raise ValueError(
            f"Unsupported or missing 'schema_version': {schema_version!r}. "
            "Expected: 1"
        )


def _load_scope(raw: Dict[str, Any], project_yaml: Path) -> Tuple[Any, Dict[str, Any]]:
    simulation = raw.get("simulation", {})
    if not isinstance(simulation, dict):
        raise ValueError("'simulation' section must be a mapping")

    external_module_path = simulation.get("external_module", None)
    if external_module_path is None:
        _check_no_external_refs(raw)
        return None, {}

    if not isinstance(external_module_path, str):
        raise ValueError("'simulation.external_module' must be a path to a Python file")

    external_path = project_yaml.parent / external_module_path
    external_module, scope = _load_external_module(external_path)
    return external_module, scope


def _build_plot_config(sim_data: Dict[str, Any]) -> PlotConfig | None:
    plots_data = sim_data.get("plots", None)
    if plots_data is None:
        return None

    if not isinstance(plots_data, list):
        raise ValueError("'simulation.plots' section must be a list")

    plot_cfg = PlotConfig(plots=plots_data)
    plot_cfg.validate()
    return plot_cfg


def _adapt_diagram_to_model_dict(
    diagram_data: Dict[str, Any],
    scope: Dict[str, Any],
) -> Dict[str, Any]:
    blocks = diagram_data.get("blocks", [])
    if not isinstance(blocks, list):
        raise ValueError("'diagram.blocks' section must be a list")

    model_blocks: list[dict[str, Any]] = []
    for desc in blocks:
        if not isinstance(desc, dict):
            raise ValueError("Each block in 'diagram.blocks' must be a mapping")

        name = desc.get("name")
        category = desc.get("category")
        block_type = desc.get("type")
        if not isinstance(name, str) or not isinstance(category, str) or not isinstance(block_type, str):
            raise ValueError(
                "Each block in 'diagram.blocks' must define string fields: "
                "'name', 'category', and 'type'"
            )

        params_raw = desc.get("parameters", {})
        if not isinstance(params_raw, dict):
            raise ValueError(
                f"'diagram.blocks[{name}].parameters' must be a mapping"
            )

        model_blocks.append(
            {
                "name": name,
                "category": category,
                "type": block_type,
                "parameters": eval_recursive(params_raw, scope),
            }
        )

    connections_raw = diagram_data.get("connections", [])
    if not isinstance(connections_raw, list):
        raise ValueError("'diagram.connections' section must be a list")

    model_connections: list[list[str]] = []
    for conn in connections_raw:
        if not isinstance(conn, dict):
            raise ValueError("Each connection in 'diagram.connections' must be a mapping")

        ports = conn.get("ports", None)
        if not isinstance(ports, list) or len(ports) != 2:
            raise ValueError(
                "Each connection in 'diagram.connections' must define "
                "'ports: [src, dst]'"
            )

        src, dst = ports
        if not isinstance(src, str) or not isinstance(dst, str):
            raise ValueError(
                "Connection ports in 'diagram.connections' must be strings"
            )
        model_connections.append([src, dst])

    return {
        "blocks": model_blocks,
        "connections": model_connections,
    }


def load_project_config(
    project_yaml: str | Path,
) -> Tuple[SimulationConfig, Dict[str, Any], PlotConfig | None, str, Path]:
    """
    Load a full pySimBlocks unified project.yaml configuration.

    Returns:
        (SimulationConfig, model_dict, PlotConfig | None, project_name, params_dir)
    """
    project_yaml = Path(project_yaml)
    raw = _load_yaml(project_yaml)

    _validate_schema_version(raw)

    external_module, scope = _load_scope(raw, project_yaml)

    resolved = _resolve_external_refs(raw, external_module) if external_module else raw

    project_data = resolved.get("project", {})
    if not isinstance(project_data, dict):
        raise ValueError("'project' section must be a mapping")
    project_name = project_data.get("name", "model")
    if not isinstance(project_name, str) or not project_name.strip():
        raise ValueError("'project.name' must be a non-empty string")

    sim_data = resolved.get("simulation", {})
    if not isinstance(sim_data, dict):
        raise ValueError("'simulation' section must be a mapping")

    required = {"dt", "T"}
    missing = required - sim_data.keys()
    if missing:
        raise ValueError(
            f"Missing required simulation parameters in 'simulation': {sorted(missing)}"
        )

    sim_eval_data = eval_recursive(sim_data, scope)
    sim_cfg = SimulationConfig(
        dt=sim_eval_data["dt"],
        T=sim_eval_data["T"],
        t0=sim_eval_data.get("t0", 0.0),
        solver=sim_eval_data.get("solver", "fixed"),
        logging=sim_data.get("logging", []),
        clock=sim_eval_data.get("clock", "internal"),
    )
    sim_cfg.validate()

    plot_cfg = _build_plot_config(sim_data)

    diagram_data = resolved.get("diagram", {})
    if not isinstance(diagram_data, dict):
        raise ValueError("'diagram' section must be a mapping")

    model_dict = _adapt_diagram_to_model_dict(diagram_data, scope)

    return sim_cfg, model_dict, plot_cfg, project_name, project_yaml.parent.resolve()
