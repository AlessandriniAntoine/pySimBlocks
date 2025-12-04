from pySimBlocks.generate.helpers import resolve_class

def generate_model(blocks, connections):
    lines = []
    imports = set()

    lines.append("import numpy as np")
    lines.append("from pySimBlocks import Model, Simulator")
    lines.append("from parameters_auto import *")
    lines.append("")

    # Entrées dynamiques des blocs
    inst_lines = []
    imports.add("# Auto imports")

    lines.append("model = Model('auto_model')\n")

    for blk in blocks:
        name = blk["name"]
        from_group = blk["from"]
        type_name = blk["type"]

        module, class_name = resolve_class(from_group, type_name)
        imports.add(f"from {module} import {class_name}")

        # paramètres = name_param
        args = []
        for key in blk:
            if key not in ["name", "type", "from"]:
                args.append(f"{key}={name}_{key}")

        inst_lines.append(f"{name} = {class_name}('{name}', {', '.join(args)})")
        inst_lines.append(f"model.add_block({name})\n")

    # Ajouter imports triés juste après les imports standard
    lines[1:1] = sorted(imports)

    lines.extend(inst_lines)

    # Connexions
    for c in connections:
        src, dst = c
        sb, sp = src.split(".")
        db, dp = dst.split(".")
        lines.append(f"model.connect('{sb}', '{sp}', '{db}', '{dp}')")

    lines.append("")
    lines.append("sim = Simulator(model, dt=dt)")

    return lines
