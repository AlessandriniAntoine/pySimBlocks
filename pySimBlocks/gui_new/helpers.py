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


# Register representer ONLY on our dumper
ModelYamlDumper.add_representer(FlowStyleList, _repr_flow_list)


# ===============================================================
# Dump helpers
# ===============================================================

def dump_yaml(data) -> str:
    """
    Dump generic YAML (parameters.yaml).
    """
    return yaml.dump(
        data,
        sort_keys=False,
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
