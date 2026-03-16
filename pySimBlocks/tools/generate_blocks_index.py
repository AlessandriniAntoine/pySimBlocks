# ******************************************************************************
#                                  pySimBlocks
#                     Copyright (c) 2026 Université de Lille & INRIA
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

import ast
import os
import yaml
from pathlib import Path


def iter_python_files(base_path):
    """Yield paths to all non-__init__ Python files under base_path.
 
    Args:
        base_path: Root directory to walk.
 
    Yields:
        Absolute path strings to .py files.
    """
    for root, _, files in os.walk(base_path):
        for f in files:
            if f.endswith(".py") and f != "__init__.py":
                yield os.path.join(root, f)


def find_block_classes(filepath: str | Path) -> list[str]:
    """Return names of all classes that inherit (directly or indirectly) from Block.
 
    Uses a name-based heuristic: a class is considered a Block subclass if
    ``"block"`` appears (case-insensitive) in its own name or in any ancestor
    name reachable within the same file.
 
    Args:
        filepath: Path to the Python source file to analyse.
 
    Returns:
        List of class names identified as Block subclasses.
    """
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

    def is_block_class(cls: str) -> bool:
        visited: set[str] = set()
        to_visit = [cls]
        while to_visit:
            current = to_visit.pop()
            if current in visited:
                continue
            visited.add(current)
            if "block" in current.lower():
                return True
            to_visit.extend(class_parents.get(current, []))
        return False

    return [cls for cls in class_parents if is_block_class(cls)]


def generate_blocks_index() -> dict:
    """Scan the blocks directory and write the YAML block index.
 
    For each block group (subdirectory of ``pySimBlocks/blocks/``), scans
    Python files, identifies Block subclasses, and records their class name
    and dotted module path. The result is written to
    ``pySimBlocks/project/pySimBlocks_blocks_index.yaml``.
 
    Returns:
        The generated index dict (mirrors the written YAML content).
    """
    blocks_dir = Path(__file__).resolve().parents[1] / "blocks"
    output_path = (
            Path(__file__).resolve().parents[1] 
            / "project" / "pySimBlocks_blocks_index.yaml"
    )

    index: dict = {}

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

            file_stem = Path(filepath).stem 

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

