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

import yaml

from pySimBlocks.gui.graphics.block_item import BlockItem
from pySimBlocks.gui.models.project_state import ProjectState


def load_yaml_file(path: str) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f) or {}


class FlowStyleList(list):
    """Marker class for YAML flow-style lists."""
    pass


class ProjectYamlDumper(yaml.SafeDumper):
    pass


def _repr_flow_list(dumper, data):
    return dumper.represent_sequence(
        "tag:yaml.org,2002:seq",
        data,
        flow_style=True,
    )


class FlowMatrix(list):
    """Marker type for matrices that must be dumped in YAML flow-style."""
    pass


def _is_matrix(obj):
    if not isinstance(obj, list):
        return False
    if not obj:
        return False
    if not all(isinstance(row, list) for row in obj):
        return False
    row_lengths = {len(row) for row in obj}
    return len(row_lengths) == 1


def _wrap_flow_matrices(obj):
    if _is_matrix(obj):
        return FlowMatrix([_wrap_flow_matrices(row) for row in obj])

    if isinstance(obj, list):
        return [_wrap_flow_matrices(x) for x in obj]

    if isinstance(obj, dict):
        return {k: _wrap_flow_matrices(v) for k, v in obj.items()}

    return obj


ProjectYamlDumper.add_representer(FlowMatrix, _repr_flow_list)
ProjectYamlDumper.add_representer(FlowStyleList, _repr_flow_list)


def dump_project_yaml(
    project_state: ProjectState | None = None,
    block_items: dict[str, BlockItem] | None = None,
    raw: dict | None = None,
) -> str:
    if raw is None:
        if project_state is None:
            raise ValueError("project_state or raw must be set")
        raw = build_project_yaml(project_state, block_items if block_items is not None else {})

    data = _wrap_flow_matrices(raw)
    return yaml.dump(
        data,
        Dumper=ProjectYamlDumper,
        sort_keys=False,
    )


def save_yaml(
    project_state: ProjectState,
    block_items: dict[str, BlockItem] | None = None,
    runtime: bool = False,
) -> None:
    directory = project_state.directory_path
    if directory is None:
        raise ValueError("project_state.directory_path must be set")

    project_raw = build_project_yaml(project_state, block_items if block_items is not None else {})
    directory.mkdir(parents=True, exist_ok=True)
    target = ".project.runtime.yaml" if runtime else "project.yaml"
    (directory / target).write_text(dump_project_yaml(raw=project_raw))


def runtime_project_yaml_path(project_dir: Path) -> Path:
    return project_dir / ".project.runtime.yaml"


def cleanup_runtime_project_yaml(project_dir: Path | None) -> None:
    if project_dir is None:
        return

    runtime_yaml = runtime_project_yaml_path(project_dir)
    if runtime_yaml.exists():
        runtime_yaml.unlink(missing_ok=True)


def _build_simulation_section(project_state: ProjectState) -> dict:
    simulation = project_state.simulation.__dict__.copy()
    if simulation.get("clock") == "internal":
        simulation.pop("clock", None)

    if project_state.external is not None:
        simulation["external_module"] = project_state.external

    simulation["logging"] = list(project_state.logging)
    simulation["plots"] = list(project_state.plots)
    return simulation


def _build_blocks_section(project_state: ProjectState) -> list[dict]:
    blocks = []
    for b in project_state.blocks:
        params = {
            k: v for k, v in b.parameters.items()
            if v is not None and b.meta.is_parameter_active(k, b.parameters)
        }
        blocks.append(
            {
                "name": b.name,
                "category": b.meta.category,
                "type": b.meta.type,
                "parameters": params,
            }
        )
    return blocks


def _build_connections_section(project_state: ProjectState) -> tuple[list[dict], dict[tuple[str, str], str]]:
    connections = []
    conn_name_map: dict[tuple[str, str], str] = {}

    for i, c in enumerate(project_state.connections, start=1):
        src = f"{c.src_block().name}.{c.src_port.name}"
        dst = f"{c.dst_block().name}.{c.dst_port.name}"
        conn_name = f"c{i}"
        conn_name_map[(src, dst)] = conn_name

        connections.append(
            {
                "name": conn_name,
                "ports": FlowStyleList([src, dst]),
            }
        )
    return connections, conn_name_map


def _build_layout_section(
    block_items: dict[str, BlockItem],
    conn_name_map: dict[tuple[str, str], str],
) -> dict:
    data: dict = {"blocks": {}}
    manual_connections = {}
    seen = set()

    for block in block_items.values():
        name = block.instance.name
        pos = block.pos()
        data["blocks"][name] = {
            "x": float(pos.x()),
            "y": float(pos.y()),
            "orientation": block.orientation,
            "width": float(block.rect().width()),
            "height": float(block.rect().height()),
        }

    if not block_items:
        return data

    view = next(iter(block_items.values())).view
    for conn in view.connections.values():
        if conn in seen:
            continue
        seen.add(conn)
        if not conn.is_manual:
            continue

        src = f"{conn.src_port.parent_block.instance.name}.{conn.src_port.instance.name}"
        dst = f"{conn.dst_port.parent_block.instance.name}.{conn.dst_port.instance.name}"
        conn_name = conn_name_map.get((src, dst), None)
        if conn_name is None:
            continue

        manual_connections[conn_name] = {
            "route": FlowStyleList([
                FlowStyleList([float(p.x()), float(p.y())])
                for p in conn.route.points
            ])
        }

    if manual_connections:
        data["connections"] = manual_connections

    return data


def build_project_yaml(
    project_state: ProjectState,
    block_items: dict[str, BlockItem] | None = None,
) -> dict:
    block_items = block_items if block_items is not None else {}
    project_name = (
        project_state.directory_path.name
        if project_state.directory_path is not None
        else "project"
    )

    blocks = _build_blocks_section(project_state)
    connections, conn_name_map = _build_connections_section(project_state)
    layout = _build_layout_section(block_items, conn_name_map)

    return {
        "schema_version": 1,
        "project": {
            "name": project_name,
            "metadata": {
                "created_by": "pySimBlocks",
                "created_at": "2026-02-18T00:00:00Z",
            },
        },
        "simulation": _build_simulation_section(project_state),
        "diagram": {
            "blocks": blocks,
            "connections": connections,
        },
        "gui": {
            "layout": layout,
        },
    }


# ---------------------------------------------------------------------
# Compatibility helpers (used by current DisplayYamlDialog)
# ---------------------------------------------------------------------
def dump_parameter_yaml(
    project_state: ProjectState | None = None,
    raw: dict | None = None,
) -> str:
    if raw is None:
        if project_state is None:
            raise ValueError("project_state or raw must be set")
        raw = _build_simulation_section(project_state)
    return yaml.dump(
        _wrap_flow_matrices(raw),
        Dumper=ProjectYamlDumper,
        sort_keys=False,
    )


def dump_model_yaml(
    project_state: ProjectState | None = None,
    raw: dict | None = None,
) -> str:
    if raw is None:
        if project_state is None:
            raise ValueError("project_state or raw must be set")
        blocks = _build_blocks_section(project_state)
        connections, _ = _build_connections_section(project_state)
        raw = {"blocks": blocks, "connections": connections}
    return yaml.dump(
        _wrap_flow_matrices(raw),
        Dumper=ProjectYamlDumper,
        sort_keys=False,
    )


def dump_layout_yaml(
    block_items: dict[str, BlockItem] | None = None,
    raw: dict | None = None,
) -> str:
    if raw is None:
        block_items = block_items if block_items is not None else {}
        raw = _build_layout_section(block_items, {})
    return yaml.dump(
        _wrap_flow_matrices(raw),
        Dumper=ProjectYamlDumper,
        sort_keys=False,
    )
