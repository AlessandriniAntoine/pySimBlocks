import os
import ast
import re
import yaml
from pathlib import Path


# ============================================================
# 1) DOCSTRING PARSING HELPERS
# ============================================================

SECTION_PATTERN = re.compile(r"^(Parameters:|Inputs:|Outputs:)$", re.MULTILINE)
ITEM_PATTERN = re.compile(r"^\s*([a-zA-Z0-9_]+)\s*:\s*(.*)$")


def extract_sections(doc):
    """Split docstring into Parameters / Inputs / Outputs sections."""
    parts = SECTION_PATTERN.split(doc)
    sections = {"Parameters": "", "Inputs": "", "Outputs": ""}

    for i in range(1, len(parts), 2):
        title = parts[i].replace(":", "")
        sections[title] = parts[i + 1].strip()

    return sections


def parse_parameters(section_text):
    """Extract block parameters with type and optional flag."""
    params = []
    for line in section_text.split("\n"):
        m = ITEM_PATTERN.match(line)
        if not m:
            continue

        name = m.group(1).strip()
        type_str = m.group(2).strip()
        optional = "(optional)" in type_str

        type_str = type_str.replace("(optional)", "").strip()

        params.append({
            "name": name,
            "optional": optional,
            "type": type_str
        })

    return params


def detect_ports(section_text):
    """Detect static ports (list) or dynamic ones."""
    lines = section_text.split("\n")

    # Case 1 – "Dynamic — specified by xxx"
    for l in lines:
        if "Dynamic" in l and "specified by" in l:
            m = re.search(r"specified by ([a-zA-Z0-9_]+)", l)
            return {
                "dynamic": "specified",
                "parameter": m.group(1) if m else None,
                "ports": []
            }

    # Case 2 – "Dynamic — in1 ... inN"
    for l in lines:
        if "Dynamic" in l and "in1" in l and "inN" in l:
            return {
                "dynamic": "indexed",
                "pattern": "in{}",
                "ports": []
            }

    # Case 3 – Static ports
    if any("(none)" in l.lower() for l in lines):
        return {"dynamic": False, "ports": []}

    ports = []
    for l in lines:
        m = ITEM_PATTERN.match(l)
        if m:
            ports.append(m.group(1).strip())

    return {
        "dynamic": False,
        "ports": ports
    }


# ============================================================
# 2) AST SCANNING
# ============================================================
def find_block_classes(filepath):
    """
    Detect classes that inherit (directly or indirectly) from any class
    whose name contains the substring 'Block'.
    Works entirely from AST without importing anything.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()

    tree = ast.parse(source)

    # Step 1 — Build local inheritance map {class: [parents]}
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

    # Step 2 — Recursive check for "Block" ancestry
    def is_block_class(cls):
        to_visit = [cls]
        visited = set()

        while to_visit:
            current = to_visit.pop()
            if current in visited:
                continue
            visited.add(current)

            # If class name contains "Block" → it is a block
            if "block" in current.lower():
                return True

            # Explore parents
            for parent in class_parents.get(current, []):
                to_visit.append(parent)

        return False

    # Step 3 — Return only block classes
    result = []
    for cls in class_parents:
        if is_block_class(cls):
            result.append({
                "class_name": cls,
                "doc": ast.get_docstring(
                    next(n for n in ast.walk(tree)
                         if isinstance(n, ast.ClassDef) and n.name == cls)
                ) or ""
            })

    return result



def iter_python_files(base_path):
    """Recursive scan for .py files."""
    for root, _, files in os.walk(base_path):
        for fname in files:
            if fname.endswith(".py") and fname != "__init__.py":
                yield os.path.join(root, fname)


# ============================================================
# 3) REGISTRY GENERATION — EXACT FORMAT EXPECTED
# ============================================================

def generate_registry():
    root = Path(__file__).resolve().parents[1]
    blocks_dir = root / "blocks"
    output_file = root / "gui" / "pySimBlocks_blocks_registry.yaml"


    registry = {}

    # Loop over block categories
    for category in os.listdir(blocks_dir):
        cat_dir = blocks_dir / category
        if not cat_dir.is_dir() or category == "__pycache__":
            continue

        # Scan recursively
        for filepath in iter_python_files(cat_dir):
            block_type = Path(filepath).stem.lower()
            classes = find_block_classes(filepath)

            if not classes:
                continue

            # Only one class per block file (pySim convention)
            cls = classes[0]
            doc = cls["doc"].strip()
            if not doc:
                continue

            sections = extract_sections(doc)

            params  = parse_parameters(sections["Parameters"])
            inputs  = detect_ports(sections["Inputs"])
            outputs = detect_ports(sections["Outputs"])

            # Remove name parameter
            params = [p for p in params if p["name"] != "name"]

            registry[block_type] = {
                "category": category,
                "inputs": inputs,
                "outputs": outputs,
                "parameters": params,
            }

    # Write final YAML
    with open(output_file, "w") as f:
        yaml.dump(registry, f, sort_keys=True)

    print(f"[OK] Registry written to {output_file}")
    return registry


if __name__ == "__main__":
    generate_registry()
