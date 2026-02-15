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

from __future__ import annotations

import importlib
import inspect
from pathlib import Path
from typing import Dict, Optional

from pySimBlocks.gui.blocks.block_meta import BlockMeta

BlockRegistry = Dict[str, Dict[str, BlockMeta]]

def load_block_registry(
    metadata_root: Path | str | None = None,    
) -> BlockRegistry:
    
    if metadata_root is None:
        metadata_root = Path(__file__).parents[1] / "gui" / "blocks"
    else:
        metadata_root = Path(metadata_root).resolve()
    
    if not metadata_root.exists():
        raise FileNotFoundError(f"blocks_metadata directory not found: {metadata_root}")
    
    registry: BlockRegistry = {}

    for py_path in metadata_root.rglob("*.py"):
        _register_block_from_py(py_path, registry)

    return registry

def _register_block_from_py(
        py_path: Path,
        registry: BlockRegistry,
) -> None:
    """
    Import a *.py file and register all BlockMeta subclasses inside.
    """

    module_name = _path_to_module(py_path)

    module = importlib.import_module(module_name)

    doc_path = _resolve_doc_path(py_path)

    for _, obj in inspect.getmembers(module, inspect.isclass):
        if not issubclass(obj, BlockMeta):
            continue
        if obj is BlockMeta:
            continue

        meta: BlockMeta = obj()

        meta.doc_path = doc_path

        category = meta.category
        block_type = meta.type

        registry.setdefault(category, {})

        if block_type in registry[category]:
            raise ValueError(
                f"Duplicate block type '{block_type}' in category '{category}'.\n"
                f"Conflict in module: {module_name}"
            )
        
        registry[category][block_type] = meta

def _path_to_module(py_path: Path) -> str:
    """
    Convert a file path to a Python module path.

    Example:
      pySimBlocks/blocks_metadata/operators/sum_meta.py
      -> pySimBlocks.blocks_metadata.operators.sum_meta
    """

    py_path = py_path.with_suffix("")

    package_root = Path(__file__).parents[1]  # pySimBlocks/

    try:
        rel_path = py_path.relative_to(package_root)
    except ValueError:
        raise RuntimeError(
            f"File {py_path} is not inside package root {package_root}"
        )

    module_name = (
        package_root.name
        + "."
        + rel_path.as_posix().replace("/", ".")
    )

    return module_name

def _resolve_doc_path(py_path: Path) -> Optional[Path]:
    """
    Resolve the documentation markdown file corresponding to a YAML metadata file.

    Example:
        blocks_metadata/systems/sofa/sofa_plant.yaml
        -> docs/blocks_metadata/systems/sofa/sofa_plant.md
    """

    try:
        parts = list(py_path.parts)
        idx = parts.index("gui")
    except ValueError:
        return None

    doc_root = Path(*parts[:idx]) / "docs"

    rel = Path(*parts[idx + 1 :]).with_suffix(".md")

    doc_path = doc_root / rel

    return doc_path if doc_path.exists() else None


if __name__ == "__main__":
    registry = load_block_registry()
