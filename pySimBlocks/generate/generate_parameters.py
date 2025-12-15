import os
import yaml

path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY_PATH = os.path.join(path, "api", "pySimBlocks_blocks_registry.yaml")

block_registry = {}
with open(REGISTRY_PATH, "r") as f:
        block_registry =  yaml.safe_load(f)

def python_array(x):
    """Convert list → np.array code."""
    return f"np.array({repr(x)})"



def generate_parameters(blocks, simulation):
    """
    Generate the parameters_auto.py file content.
    """

    lines = ["import numpy as np\n"]

    # ------------------------------------------------------------
    # 1. Block parameters (READ FROM BLOCK DICT ITSELF)
    # ------------------------------------------------------------
    for blk in blocks:
        name = blk["name"]
        block_type = blk["type"]

        # registry parameter types
        reg_params = {
            p["name"]: p["type"]
            for p in block_registry[block_type]["parameters"]
        }

        for key, value in blk.items():

            # skip structural keys
            if key in ["name", "type", "from"]:
                continue

            varname = f"{name}_{key}"
            declared_type = reg_params.get(key, "")

            # list → numpy array
            if isinstance(value, list):
                lines.append(f"{varname} = np.array({repr(value)})")

            # string parameters declared as str → quoted
            elif isinstance(value, str) and declared_type == "str":
                lines.append(f"{varname} = {repr(value)}")

            # string expressions (sample_time, etc.)
            elif isinstance(value, str):
                lines.append(f"{varname} = {value}")

            # numeric / others
            else:
                lines.append(f"{varname} = {repr(value)}")

        lines.append("")

    # ------------------------------------------------------------
    # 2. Simulation parameters
    # ------------------------------------------------------------
    dt = simulation.get("dt")
    T = simulation.get("T")

    lines.append(f"dt = {dt if isinstance(dt, str) else repr(dt)}")
    lines.append(f"T = {T if isinstance(T, str) else repr(T)}")

    return lines
