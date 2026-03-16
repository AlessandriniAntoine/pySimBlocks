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

# Mapping: category -> block_type -> BlockMeta instance.
BlockRegistry = Dict[str, Dict[str, BlockMeta]]


def load_block_registry(
    metadata_root: Path | str | None = None,    
) -> BlockRegistry:
    """Load all BlockMeta subclasses from the GUI blocks directory.
 
    Recursively scans metadata_root for Python files and registers every
    BlockMeta subclass found. Defaults to ``pySimBlocks/gui/blocks/``.
 
    Args:
        metadata_root: Root directory to scan. Defaults to the package's
            ``gui/blocks/`` directory.
 
    Returns:
        Registry mapping category names to dicts of block_type -> BlockMeta.
 
    Raises:
        FileNotFoundError: If metadata_root does not exist.
        ValueError: If two files define a BlockMeta with the same type
            within the same category.
    """
    if metadata_root is None:
        metadata_root = Path(__file__).parents[1] / "gui" / "blocks"
    else:
        metadata_root = Path(metadata_root).resolve()
    
    if not metadata_root.exists():
        raise FileNotFoundError(
                f"blocks_metadata directory not found: {metadata_root}"
                )
    
    registry: BlockRegistry = {}

    for py_path in metadata_root.rglob("*.py"):
        _register_block_from_py(py_path, registry)

    return registry


# --------------------------------------------------------------------------
# Private helpers
# --------------------------------------------------------------------------
 
def _register_block_from_py(
        py_path: Path,
        registry: BlockRegistry,
) -> None:
    """Import a .py file and register all BlockMeta subclasses it contains."""
    module_name = _path_to_module(py_path)
    module = importlib.import_module(module_name)
    doc_path = _resolve_doc_path(py_path)

    for _, obj in inspect.getmembers(module, inspect.isclass):
        if not issubclass(obj, BlockMeta) or obj is BlockMeta:
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
    """Convert a file path to a dotted Python module name.
 
    Example:
        ``pySimBlocks/gui/blocks/operators/sum.py``
        -> ``pySimBlocks.gui.blocks.operators.sum``
 
    Args:
        py_path: Absolute path to a Python source file.
 
    Returns:
        Dotted module name relative to the package root.
 
    Raises:
        RuntimeError: If py_path is not inside the package root.
    """    
    py_path = py_path.with_suffix("")
    package_root = Path(__file__).parents[1]  # pySimBlocks/

    try:
        rel_path = py_path.relative_to(package_root)
    except ValueError:
        raise RuntimeError(
            f"File {py_path} is not inside package root {package_root}"
        )

    return package_root.name + "." + rel_path.as_posix().replace("/", ".")


def _resolve_doc_path(py_path: Path) -> Optional[Path]:
    """Resolve the Markdown documentation file for a GUI block module.
 
    Example:
        ``gui/blocks/systems/sofa/sofa_plant.py``
        -> ``docs/blocks/systems/sofa/sofa_plant.md``
 
    Args:
        py_path: Path to the GUI block Python file.
 
    Returns:
        Path to the corresponding .md file if it exists, else None.
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
