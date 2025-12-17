import os
import yaml
import ast
from pathlib import Path

def iter_python_files(base_path):
    for root, _, files in os.walk(base_path):
        for f in files:
            if f.endswith(".py") and f != "__init__.py":
                yield os.path.join(root, f)


def find_block_classes(filepath):
    """Find all classes inheriting directly or indirectly from 'Block'."""
    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()

    tree = ast.parse(source)

    class_parents = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            parents = []
            for base in node.bases:
                if isinstance(base, ast.Name):
                    parents.append(base.id)
                elif isinstance(base, ast.Attribute):
                    parents.append(base.attr)
            class_parents[node.name] = parents

    def is_block_class(cls):
        visited = set()
        to_visit = [cls]

        while to_visit:
            current = to_visit.pop()
            if current in visited:
                continue
            visited.add(current)

            if "block" in current.lower():
                return True

            parents = class_parents.get(current, [])
            to_visit.extend(parents)

        return False

    block_classes = []
    for cls in class_parents:
        if is_block_class(cls):
            block_classes.append(cls)

    return block_classes


def generate_blocks_index():
    blocks_dir = Path(__file__).resolve().parents[1] / "blocks"
    output_path = Path(__file__).resolve().parents[1] / "project" / "pySimBlocks_blocks_index.yaml"

    index = {}

    for group in os.listdir(blocks_dir):
        group_path = blocks_dir / group

        if (
            not group_path.is_dir()
            or group.startswith("_")
            or group.startswith(".")
            or group == "__pycache__"
        ):
            continue

        index[group] = {}

        for filepath in iter_python_files(group_path):
            classes = find_block_classes(filepath)
            if not classes:
                continue

            file_stem = Path(filepath).stem  # snake_case name → key in YAML

            # Compute module path
            rel_path = filepath.split("pySimBlocks")[-1].lstrip("/\\")
            module_path = "pySimBlocks." + rel_path.replace("/", ".").replace("\\", ".").removesuffix(".py")

            # Only one block class per file (pySimBlocks rule)
            class_name = classes[0]

            index[group][file_stem] = {
                "class": class_name,
                "module": module_path
            }

    with open(output_path, "w") as f:
        yaml.dump(index, f, sort_keys=True)

    print(f"[OK] Block index written to {output_path}")
    return index


if __name__ == "__main__":
    generate_blocks_index()
