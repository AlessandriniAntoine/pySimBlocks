from pathlib import Path
import os
import yaml
from pySimBlocks.gui.model.project_state import ProjectState


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
def dump_parameter_yaml(project=None, raw:dict|None=None):
    if project:
        data = build_parameters_yaml(project)
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

def dump_model_yaml(project=None, raw:dict|None=None) -> str:
    if project:
        data = build_model_yaml(project)
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

def save_yaml(project: ProjectState, temp=False):
    directory = project.directory_path
    params_yaml = build_parameters_yaml(project)
    model_yaml = build_model_yaml(project)

    if temp:
        temp_dir = directory / ".temp"
        if "external" in params_yaml:
            external_abs = directory / params_yaml["external"]
            external_temp = os.path.relpath(external_abs, temp_dir)
            params_yaml["external"] = external_temp
        directory = temp_dir

    directory.mkdir(parents=True, exist_ok=True)
    (directory / "parameters.yaml").write_text(
        dump_parameter_yaml(raw=params_yaml)
    )
    (directory / "model.yaml").write_text(
        dump_model_yaml(raw=model_yaml)
    )

# ===============================================================
# Build function
# ===============================================================
def build_parameters_yaml(project: ProjectState) -> dict:
    data = {
        "simulation": project.simulation,
        "blocks": {},
        "logging": project.logging,
        "plots": project.plots,
    }

    for b in project.blocks:
        params = {
            k: v for k, v in b.parameters.items()
            if v is not None
        }
        data["blocks"][b.name] = params

    if project.external is not None:
        data["external"] = project.external

    return data


def build_model_yaml(project: ProjectState) -> dict:
    return {
        "blocks": [
            {
                "name": b.name,
                "category": b.meta.category,
                "type": b.meta.type,
            }
            for b in project.blocks
        ],
        "connections": [
             [f"{c.src_block.name}.{c.src_port}",
              f"{c.dst_block.name}.{c.dst_port}",
            ]
            for c in project.connections
        ],
    }
