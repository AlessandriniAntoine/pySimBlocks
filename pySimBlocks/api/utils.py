import yaml
import numpy as np
import os

path_dir = os.path.dirname(os.path.abspath(__file__))
REGISTRY_PATH = "pySim_blocks_registry.yaml"
REGISTRY_PATH = os.path.join(path_dir, REGISTRY_PATH)

def load_registry():
    with open(REGISTRY_PATH, "r") as f:
        return yaml.safe_load(f)

# -------- Flow style YAML --------
class FlowStyleList(list):
    pass

def flow_representer(dumper, data):
    return dumper.represent_sequence(
        "tag:yaml.org,2002:seq", data, flow_style=True
    )

yaml.add_representer(FlowStyleList, flow_representer)

# -------- Array parser --------
def parse_array(text):
    if text is None or text.strip() == "":
        return None
    text = text.strip()

    # simple list
    if "," in text and "[" not in text and ";" not in text:
        try:
            return [float(x.strip()) for x in text.split(",")]
        except:
            pass

    # python literal
    try:
        val = eval(text, {"__builtins__":{}})
        return np.array(val).tolist()
    except:
        pass

    # semicolon matrix
    if ";" in text:
        rows = text.split(";")
        return [list(map(float, r.split(","))) for r in rows]

    return text
