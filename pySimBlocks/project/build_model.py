# ******************************************************************************
#                                 pySimBlocks                                 
#                Copyright (c) 2026 The pySimBlocks Authors               
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

import importlib
from pathlib import Path
import yaml
from typing import Dict, Any

from pySimBlocks.core.model import Model
from pySimBlocks.core.config import ModelConfig

# ============================================================
# Metadata lazy cache
# ============================================================

_METADATA_CACHE: dict[str, dict] = {}


def _metadata_path_from_module(module: str) -> Path:
    """
    Convert a block python module path into its metadata yaml path.

    Example:
        pySimBlocks.blocks.operators.algebraic_function
        -> pySimBlocks/blocks_metadata/operators/algebraic_function.yaml
    """
    parts = module.split(".")
    parts[1] = "blocks_metadata"
    return Path(__file__).parents[2].joinpath(*parts).with_suffix(".yaml")


def _get_block_metadata(block_info: dict) -> dict:
    """
    Lazy-load and cache block metadata.
    """
    module = block_info["module"]

    if module in _METADATA_CACHE:
        return _METADATA_CACHE[module]

    meta_path = _metadata_path_from_module(module)

    if meta_path.exists():
        with meta_path.open("r") as f:
            meta = yaml.safe_load(f) or {}
    else:
        meta = {}

    _METADATA_CACHE[module] = meta
    return meta


def _apply_block_adapter(
    block_type: str,
    params: dict,
    *,
    parameters_dir: Path | None,
) -> dict:
    """
    Dynamically import and apply a block adapter.

    Adapter naming convention:
        <block_type>_adapter in pySimBlocks.project.block_adapter
    """
    if parameters_dir is None:
        raise RuntimeError(
            f"Adapter required for block '{block_type}' "
            "but ModelConfig.parameters_dir is not set"
        )

    adapter_module_name = (
        f"pySimBlocks.project.block_adapter.{block_type}_adapter"
    )

    try:
        adapter_module = importlib.import_module(adapter_module_name)
    except ImportError as e:
        raise ImportError(
            f"Block '{block_type}' requires an adapter but "
            f"no adapter module '{adapter_module_name}' was found"
        ) from e

    adapter_func_name = f"{block_type}_adapter"
    try:
        adapter_func = getattr(adapter_module, adapter_func_name)
    except AttributeError as e:
        raise AttributeError(
            f"Adapter module '{adapter_module_name}' must define "
            f"function '{adapter_func_name}'"
        ) from e

    return adapter_func(
        params,
        parameters_dir=parameters_dir,
    )


# ============================================================
# Public API
# ============================================================

def build_model_from_yaml(
    model: Model,
    model_yaml: Path,
    model_cfg: ModelConfig | None,
) -> None:
    """
    Build a Model instance from a model.yaml file.
    """
    with model_yaml.open("r") as f:
        model_data = yaml.safe_load(f) or {}

    build_model_from_dict(model, model_data, model_cfg)


def build_model_from_dict(
    model: Model,
    model_data: Dict[str, Any],
    model_cfg: ModelConfig | None,
) -> None:
    """
    Build a Model instance from an already loaded model dictionary.
    """

    # ------------------------------------------------------------
    # Load block registry
    # ------------------------------------------------------------
    index_path = Path(__file__).parent / "pySimBlocks_blocks_index.yaml"
    with index_path.open("r") as f:
        blocks_index = yaml.safe_load(f) or {}

    # ------------------------------------------------------------
    # Instantiate blocks
    # ------------------------------------------------------------
    for desc in model_data.get("blocks", []):
        name = desc["name"]
        category = desc["category"]
        block_type = desc["type"]

        try:
            block_info = blocks_index[category][block_type]
        except KeyError:
            raise ValueError(
                f"Unknown block '{block_type}' in category '{category}'."
            )

        # --------------------------------------------------------
        # Load Python block class
        # --------------------------------------------------------
        module = importlib.import_module(block_info["module"])
        BlockClass = getattr(module, block_info["class"])

        # --------------------------------------------------------
        # Load parameters
        # --------------------------------------------------------
        has_inline_params = "parameters" in desc

        if model_cfg is not None:
            if has_inline_params:
                raise ValueError(
                    f"Block '{name}' defines inline parameters but a ModelConfig "
                    f"is also provided. Choose exactly one source of parameters."
                )
            params = (
                model_cfg.get_block_params(name)
                if model_cfg.has_block(name)
                else {}
            )
        else:
            params = desc.get("parameters", {})

        # --------------------------------------------------------
        # Lazy metadata + adapter handling
        # --------------------------------------------------------
        metadata = _get_block_metadata(block_info)
        needs_adapter = (
            metadata
            .get("execution", {})
            .get("adapter", False)
        )

        if needs_adapter:
            params = _apply_block_adapter(
                block_type=block_type,
                params=params,
                parameters_dir=model_cfg.parameters_dir if model_cfg else None,
            )

        # --------------------------------------------------------
        # Instantiate block
        # --------------------------------------------------------
        block = BlockClass(name=name, **params)
        model.add_block(block)

    # ------------------------------------------------------------
    # Connections
    # ------------------------------------------------------------
    for src, dst in model_data.get("connections", []):
        src_block, src_port = src.split(".")
        dst_block, dst_port = dst.split(".")
        model.connect(src_block, src_port, dst_block, dst_port)

