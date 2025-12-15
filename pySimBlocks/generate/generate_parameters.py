def python_array(x):
    """Convert list → np.array code."""
    return f"np.array({repr(x)})"

def generate_parameters(blocks, simulation):
    """
    Generate the parameters_auto.py file content.
    """

    lines = ["import numpy as np\n"]

    # ------------------------------------------------------------
    # 1. Block parameters
    # ------------------------------------------------------------
    for blk in blocks:
        name = blk["name"]

        for key, value in blk.items():
            if key in ["name", "type", "from"]:
                continue

            varname = f"{name}_{key}"

            # Lists → numpy arrays
            if isinstance(value, list):
                lines.append(f"{varname} = np.array({repr(value)})")

            # Expressions (strings) → write as Python expression
            elif isinstance(value, str):
                lines.append(f"{varname} = {value}")

            # Numeric / others
            else:
                lines.append(f"{varname} = {repr(value)}")

        lines.append("")

    # ------------------------------------------------------------
    # 2. Simulation parameters
    # ------------------------------------------------------------
    dt = simulation.get("dt")
    T = simulation.get("T")

    if isinstance(dt, str):
        lines.append(f"dt = {dt}")
    else:
        lines.append(f"dt = {repr(dt)}")

    if isinstance(T, str):
        lines.append(f"T = {T}")
    else:
        lines.append(f"T = {repr(T)}")

    return lines
