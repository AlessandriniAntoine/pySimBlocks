# ******************************************************************************
#                                  pySimBlocks
#                     Copyright (c) 2026 Antoine Alessandrini
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
import os
import yaml
from pySimBlocks.gui.model.project_state import ProjectState
from pySimBlocks.gui.graphics.block_item import BlockItem


def load_yaml_file(path: str) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f) or {}
# ===============================================================
# Custom list type for flow-style sequences
# ===============================================================
class FlowStyleList(list):
    """Marker class for YAML flow-style lists."""
    pass


class ModelYamlDumper(yaml.SafeDumper):
    pass


def _repr_flow_list(dumper, data):
    return dumper.represent_sequence(
        "tag:yaml.org,2002:seq",
        data,
        flow_style=True,
    )



class FlowMatrix(list):
    """
    Marker type for matrices that must be dumped in YAML flow-style.
    """
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
    """
    Recursively wrap matrices into FlowMatrix for YAML dumping.
    """
    if _is_matrix(obj):
        return FlowMatrix([_wrap_flow_matrices(row) for row in obj])

    if isinstance(obj, list):
        return [_wrap_flow_matrices(x) for x in obj]

    if isinstance(obj, dict):
        return {k: _wrap_flow_matrices(v) for k, v in obj.items()}

    return obj

ModelYamlDumper.add_representer(FlowMatrix, _repr_flow_list)
ModelYamlDumper.add_representer(FlowStyleList, _repr_flow_list)
# ===============================================================
# Dump helpers
# ===============================================================
def dump_parameter_yaml(
        project_state: ProjectState | None = None, 
        raw: dict | None = None
        ) -> str:
    if project_state:
        data = build_parameters_yaml(project_state)
    elif raw:
        data = raw
    else:
        raise ValueError("project or raw must be set")

    data = _wrap_flow_matrices(data)

    return yaml.dump(
        data,
        Dumper=ModelYamlDumper,
        sort_keys=False
    )

def dump_model_yaml(
        project_state: ProjectState | None = None, 
        raw: dict | None = None
        ) -> str:
    if project_state:
        data = build_model_yaml(project_state)
    elif raw:
        data = raw
    else:
        raise ValueError("project or raw must be set")

    if "connections" in data:
        data["connections"] = [
            FlowStyleList(conn) for conn in data["connections"]
        ]

    return yaml.dump(
        data,
        Dumper=ModelYamlDumper,
        sort_keys=False,
    )

def dump_layout_yaml(
        block_items: dict[str, BlockItem] | None = None, 
        raw: dict | None = None
        ) -> str:
    if block_items is not None:
        data = build_layout_yaml(block_items)
    elif raw:
        data = raw
    else:
        raise ValueError("block_items or raw must be set")
    
    return yaml.dump(
        data,
        Dumper=ModelYamlDumper,
        sort_keys=False,
    )

# ===============================================================
# Save functions
# ===============================================================
def save_yaml(
        project_state: ProjectState, 
        block_items: dict[str, BlockItem] | None = None, 
        temp: bool = False) -> None:
    
    directory = project_state.directory_path
    params_yaml = build_parameters_yaml(project_state)
    model_yaml = build_model_yaml(project_state)

    if temp:
        temp_dir = directory / ".temp"
        if "external" in params_yaml:
            external_abs = directory / params_yaml["external"]
            external_temp = os.path.relpath(external_abs, temp_dir)
            params_yaml["external"] = external_temp
        directory = temp_dir
    
    directory.mkdir(parents=True, exist_ok=True)

    (directory / "parameters.yaml").write_text(dump_parameter_yaml(raw=params_yaml))
    (directory / "model.yaml").write_text(dump_model_yaml(raw=model_yaml))
    if not temp and block_items:
        layout_yaml = build_layout_yaml(block_items)
        (directory / "layout.yaml").write_text(dump_layout_yaml(raw=layout_yaml))
    
# ===============================================================
# Build function
# ===============================================================
def build_parameters_yaml(project_state: ProjectState) -> dict:
    data = {
        "simulation": project_state.simulation.__dict__,
        "blocks": {},
        "logging": project_state.logging,
        "plots": project_state.plots,
    }

    for b in project_state.blocks:
        params = {
            k: v for k, v in b.parameters.items()
            if v is not None
        }
        data["blocks"][b.name] = params

    if project_state.external is not None:
        data["external"] = project_state.external

    return data


def build_model_yaml(project_state: ProjectState) -> dict:
    return {
        "blocks": [
            {
                "name": b.name,
                "category": b.meta.category,
                "type": b.meta.type,
            }
            for b in project_state.blocks
        ],
        "connections": [
             [f"{c.src_block().name}.{c.src_port.name}",
              f"{c.dst_block().name}.{c.dst_port.name}",
            ]
            for c in project_state.connections
        ],
    }

def build_layout_yaml(block_items: dict[str, BlockItem]) -> dict:
    """
    Build layout.yaml content from the current diagram view.

    This function extracts ONLY visual information.
    """

    data = {
        "version": 1,
        "blocks": {}
    }

    for item in block_items.values():
        name = item.instance.name
        pos = item.pos()
        data["blocks"][name] = {
            "x": float(pos.x()),
            "y": float(pos.y()),
        }

    return data

