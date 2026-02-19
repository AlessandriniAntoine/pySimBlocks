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

import importlib
from pathlib import Path
from typing import Dict, Any
import yaml

from pySimBlocks.core.model import Model

# ============================================================
# Public API
# ============================================================


def build_model_from_dict(
    model: Model,
    model_data: Dict[str, Any],
    params_dir: Path | None = None,
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

        print(desc)

        try:
            block_info = blocks_index[category][block_type]
        except KeyError:
            print(f"Available blocks in category '{category}':")
            for bt in blocks_index.get(category, {}):
                print(f"  - {bt}")
            print(desc)
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
        params = desc.get("parameters", {})

        # --------------------------------------------------------
        # Instantiate block
        # --------------------------------------------------------
        params = BlockClass.adapt_params(params, params_dir=params_dir)
        block = BlockClass(name=name, **params)
        model.add_block(block)

    # ------------------------------------------------------------
    # Connections
    # ------------------------------------------------------------
    for src, dst in model_data.get("connections", []):
        src_block, src_port = src.split(".")
        dst_block, dst_port = dst.split(".")
        model.connect(src_block, src_port, dst_block, dst_port)
