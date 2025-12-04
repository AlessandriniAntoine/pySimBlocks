import os
import re
import yaml
import importlib
import inspect


# ------------------------------------------------------------
# Utilities for docstring parsing
# ------------------------------------------------------------

SECTION_PATTERN = re.compile(r"^(Parameters:|Inputs:|Outputs:)$", re.MULTILINE)

ITEM_PATTERN = re.compile(
    r"^\s*([a-zA-Z0-9_]+)\s*:\s*([^\n]+)$"
)


def extract_sections(doc):
    """
    Split the docstring into sections:
        Parameters:
        Inputs:
        Outputs:
    Return:
        dict { "Parameters": str, "Inputs": str, "Outputs": str }
    """
    parts = SECTION_PATTERN.split(doc)
    # parts = ["text before", "SectionName", "text", "SectionName", "text", ...]

    sections = {"Parameters": "", "Inputs": "", "Outputs": ""}

    for i in range(1, len(parts), 2):
        title = parts[i].replace(":", "")
        content = parts[i+1]
        sections[title] = content.strip()

    return sections


def parse_items(section_text):
    """
    Parse items inside a section such as:

        gain: float
            Gain value
        x0: array (n,1) (optional)

    Return list of dicts:
        [
            {"name": "gain", "type": "float", "optional": False},
            {"name": "x0", "type": "array (n,1)", "optional": True}
        ]
    """
    items = []

    lines = section_text.split("\n")
    for line in lines:
        m = ITEM_PATTERN.match(line)
        if not m:
            continue

        name = m.group(1).strip()
        type_str = m.group(2).strip()

        optional = "(optional)" in type_str
        type_str = type_str.replace("(optional)", "").strip()

        items.append({
            "name": name,
            "type": type_str,
            "optional": optional,
        })

    return items


def detect_dynamic_inputs(input_items):
    """
    Detect inputs like in1, in2, inN.
    If 'inN' appears, treat inputs as dynamic:
        pattern = "in{}"
    """
    names = [item["name"] for item in input_items]

    # Case 1: No dynamic marker -> fixed ports
    if "inN" not in names:
        return {"dynamic": False, "ports": names}

    # Case 2: Dynamic input list
    return {"dynamic": True, "pattern": "in{}"}


# ------------------------------------------------------------
# Block discovery and import
# ------------------------------------------------------------

def discover_blocks(base_path):
    """
    Scan pySimBlocks/blocks and import each block class.
    Return list of tuples:
        (category, block_type, class_object)
    """
    blocks = []

    for category in os.listdir(base_path):
        if category == "__pycache__":
            continue

        cat_dir = os.path.join(base_path, category)
        if not os.path.isdir(cat_dir):
            continue

        for file in os.listdir(cat_dir):
            if not file.endswith(".py") or file == "__init__.py":
                continue

            block_type = file.replace(".py", "")
            module_path = f"pySimBlocks.blocks.{category}.{block_type}"

            try:
                module = importlib.import_module(module_path)
            except Exception as e:
                print(f"Could not import {module_path}: {e}")
                continue

            # find the class that inherits from Block
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if obj.__module__ != module_path:
                    continue
                if "Block" in [base.__name__ for base in inspect.getmro(obj)[1:]]:
                    blocks.append((category, block_type, obj))
                    break

    return blocks


# ------------------------------------------------------------
# Registry generation
# ------------------------------------------------------------

def generate_registry(output_path="pySim_blocks_registry.yaml"):
    base_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "blocks")
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), output_path)

    blocks = discover_blocks(base_path)

    registry = {}

    for category, block_type, cls in blocks:

        doc = inspect.getdoc(cls)
        if not doc:
            continue

        sections = extract_sections(doc)

        params = parse_items(sections["Parameters"])
        inputs = detect_dynamic_inputs(parse_items(sections["Inputs"]))
        outputs = parse_items(sections["Outputs"])

        params = [p for p in params if p["name"] != "name"]

        registry[block_type] = {
            "category": category,
            "parameters": params,
            "inputs": inputs,
            "outputs": [item["name"] for item in outputs],
        }

    # Write YAML
    with open(output_path, "w") as f:
        yaml.dump(registry, f, sort_keys=True)

    print(f"Registry successfully written to {output_path}")


if __name__ == "__main__":
    generate_registry()
