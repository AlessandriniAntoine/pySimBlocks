import importlib
import os
from pathlib import Path
import yaml

from pySimBlocks.core.model import Model
from pySimBlocks.core.config import ModelConfig


def build_model(
    model: Model,
    model_yaml: Path,
    model_cfg: ModelConfig | None,
) -> None:

    # ------------------------------------------------------------
    # Load block registry
    # ------------------------------------------------------------
    index_path = Path(__file__).parent / "pySimBlocks_blocks_index.yaml"
    with index_path.open("r") as f:
        blocks_index = yaml.safe_load(f) or {}

    # ------------------------------------------------------------
    # Load model.yaml
    # ------------------------------------------------------------
    with Path(model_yaml).open("r") as f:
        data = yaml.safe_load(f) or {}

    # ------------------------------------------------------------
    # Instantiate blocks
    # ------------------------------------------------------------
    for desc in data.get("blocks", []):
        name = desc["name"]
        category = desc["from"]
        block_type = desc["type"]

        # ---------------- Registry lookup ----------------
        try:
            block_info = blocks_index[category][block_type]
        except KeyError:
            raise ValueError(
                f"Unknown block '{block_type}' in category '{category}'"
            )

        module_path = block_info["module"]
        class_name = block_info["class"]

        module = importlib.import_module(module_path)
        BlockClass = getattr(module, class_name)

        # ---------------- Parameters resolution ----------------
        has_inline_params = "parameters" in desc

        if model_cfg is not None:
            if has_inline_params:
                raise ValueError(
                    f"Block '{name}' defines inline parameters in model.yaml "
                    f"but a ModelConfig is also provided. "
                    f"Choose exactly one source of parameters."
                )
            params = (
                model_cfg.get_block_params(name)
                if model_cfg.has_block(name)
                else {}
            )
        else:
            params = desc.get("parameters", {})

        # ---------------- Block instantiation ----------------
        block = BlockClass(name=name, **params)
        model.add_block(block)


    # ------------------------------------------------------------
    # Connections
    # ------------------------------------------------------------
    for src, dst in data.get("connections", []):
        src_block, src_port = src.split(".")
        dst_block, dst_port = dst.split(".")

        model.connect(src_block, src_port, dst_block, dst_port)
