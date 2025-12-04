from pySimBlocks.generate.helpers import python_array


def generate_parameters(blocks, simulation):
    lines = ["import numpy as np\n"]

    for blk in blocks:
        name = blk["name"]
        for key, value in blk.items():
            if key in ["name", "type", "from"]:
                continue

            varname = f"{name}_{key}"

            if isinstance(value, list):
                lines.append(f"{varname} = {python_array(value)}")
            else:
                lines.append(f"{varname} = {repr(value)}")

        lines.append("")

    lines.append(f"dt = {simulation['dt']}")
    lines.append(f"T = {simulation['T']}")

    return lines
