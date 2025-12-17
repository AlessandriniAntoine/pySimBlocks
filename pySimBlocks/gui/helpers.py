import yaml


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

def dump_yaml(data):
    data = _wrap_flow_matrices(data)
    return yaml.dump(
        data,
        Dumper=ModelYamlDumper,
        sort_keys=False
    )



def dump_model_yaml(model_yaml: dict) -> str:
    """
    Dump model.yaml with:
    - blocks in block-style
    - connections in flow-style
    """
    data = dict(model_yaml)

    if "connections" in data:
        data["connections"] = [
            FlowStyleList(conn) for conn in data["connections"]
        ]

    return yaml.dump(
        data,
        Dumper=ModelYamlDumper,
        sort_keys=False,
    )

def parse_yaml_value(raw: str):
    raw = raw.strip()

    # Empty → parameter not set
    if raw == "":
        return None

    # Reference (special syntax)
    if raw.startswith("@"):
        return raw

    # Everything else → MUST be parsed as YAML
    try:
        return yaml.safe_load(raw)
    except Exception:
        raise ValueError(f"Invalid value: {raw}")
