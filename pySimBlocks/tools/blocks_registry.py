from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, Optional
import yaml


@dataclass(frozen=True)
class BlockMeta:
    """
    In-memory representation of a block metadata entry.
    This is the ONLY source of truth for the GUI.
    """
    name: str
    category: str
    type: str

    summary: str
    description: str

    parameters: Dict[str, Any]
    ports: Dict[list, Any]

    execution: Dict[str, Any]
    notes: Optional[list[str]]

    # Paths (useful for GUI help & debugging)
    yaml_path: Path
    doc_path: Optional[Path]

BlockRegistry = Dict[str, Dict[str, BlockMeta]]

def load_block_registry(
    metadata_root: Path | str | None = None,
) -> BlockRegistry:
    """
    Load all block metadata YAML files into an in-memory registry.

    The directory is scanned recursively.
    Expected structure (example):

        blocks_metadata/
            controllers/
                pid.yaml
            operators/
                gain.yaml
                sum.yaml
            systems/
                sofa/
                    sofa_plant.yaml

    The category is taken from the YAML content (not the folder name),
    but the folder structure is preserved for plugins (e.g. sofa).

    Returns
    -------
    BlockRegistry
        Nested dict: registry[category][type] -> BlockMeta
    """

    if metadata_root is None:
        metadata_root = Path(__file__).parents[1] / "blocks_metadata"
    else:
        metadata_root = Path(metadata_root).resolve()

    if not metadata_root.exists():
        raise FileNotFoundError(f"blocks_metadata directory not found: {metadata_root}")

    registry: BlockRegistry = {}

    for yaml_path in metadata_root.rglob("*.yaml"):
        _register_block_from_yaml(yaml_path, registry)

    return registry


def _register_block_from_yaml(
    yaml_path: Path,
    registry: BlockRegistry,
) -> None:
    """
    Parse one block YAML file and insert it into the registry.
    """

    data = yaml.safe_load(yaml_path.read_text())

    if not isinstance(data, dict):
        raise ValueError(f"Invalid YAML format: {yaml_path}")

    # ------------------------------------------------------------------
    # Mandatory fields (fail fast)
    # ------------------------------------------------------------------
    for key in ("name", "category", "type", "summary", "description"):
        if key not in data:
            raise KeyError(f"Missing required field '{key}' in {yaml_path}")

    name = data["name"]
    category = data["category"]
    block_type = data["type"]

    # ------------------------------------------------------------------
    # Optional sections (normalized)
    # ------------------------------------------------------------------
    parameters = data.get("parameters", {})
    ports = data.get("ports", {})
    execution = data.get("execution", {})
    notes = data.get("notes", None)

    # ------------------------------------------------------------------
    # Documentation (.md) resolution
    # Mirrors the metadata folder structure
    # ------------------------------------------------------------------
    doc_path = _resolve_doc_path(yaml_path)

    # ------------------------------------------------------------------
    # Registry insertion
    # ------------------------------------------------------------------
    registry.setdefault(category, {})

    if block_type in registry[category]:
        raise ValueError(
            f"Duplicate block type '{block_type}' in category '{category}'.\n"
            f"Conflict at: {yaml_path}"
        )

    registry[category][block_type] = BlockMeta(
        name=name,
        category=category,
        type=block_type,
        summary=data["summary"],
        description=data["description"],
        parameters=parameters,
        ports=ports,
        execution=execution,
        notes=notes,
        yaml_path=yaml_path,
        doc_path=doc_path,
    )


def _resolve_doc_path(yaml_path: Path) -> Optional[Path]:
    """
    Resolve the documentation markdown file corresponding to a YAML metadata file.

    Example:
        blocks_metadata/systems/sofa/sofa_plant.yaml
        -> docs/blocks_metadata/systems/sofa/sofa_plant.md
    """

    try:
        parts = list(yaml_path.parts)
        idx = parts.index("blocks_metadata")
    except ValueError:
        return None

    doc_root = Path(*parts[:idx]) / "docs" / "blocks"
    rel = Path(*parts[idx + 1 :]).with_suffix(".md")
    doc_path = doc_root / rel

    return doc_path if doc_path.exists() else None


if __name__ == "__main__":
    registry = load_block_registry()

    # for category, blocks in registry.items():
    #     for block_type, meta in blocks.items():
    #         print(meta.name)
