import importlib
from pathlib import Path
import yaml
from typing import Dict, Any

from pySimBlocks.core.model import Model
from pySimBlocks.core.config import ModelConfig


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

    Parameters
    ----------
    model : Model
        Target model instance to populate.

    model_data : dict
        Parsed content of model.yaml.

    model_cfg : ModelConfig or None
        Numerical parameters for blocks.
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

        module = importlib.import_module(block_info["module"])
        BlockClass = getattr(module, block_info["class"])

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

        block = BlockClass(name=name, **params)
        model.add_block(block)

    # ------------------------------------------------------------
    # Connections
    # ------------------------------------------------------------
    for src, dst in model_data.get("connections", []):
        src_block, src_port = src.split(".")
        dst_block, dst_port = dst.split(".")
        model.connect(src_block, src_port, dst_block, dst_port)



def adapt_model_for_sofa(model_yaml: Path) -> Dict[str, Any]:
    """
    Load model.yaml and adapt it for SOFA execution.

    This replaces any SofaPlant block by a SofaExchangeIO block,
    while preserving block name and connections.

    Parameters
    ----------
    model_yaml : Path
        Path to model.yaml

    Returns
    -------
    dict
        Adapted model dictionary
    """
    with model_yaml.open("r") as f:
        model_data = yaml.safe_load(f) or {}

    adapted = dict(model_data)
    adapted_blocks = []

    for block in model_data.get("blocks", []):
        if block["type"].lower() == "sofa_plant":
            adapted_blocks.append({
                "name": block["name"],
                "category": "systems",
                "type": "sofa_exchange_i_o",
            })
        else:
            adapted_blocks.append(block)

    adapted["blocks"] = adapted_blocks
    return adapted
