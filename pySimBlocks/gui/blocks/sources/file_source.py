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

from typing import Any, Dict

from pySimBlocks.gui.blocks.block_meta import BlockMeta
from pySimBlocks.gui.blocks.parameter_meta import ParameterMeta
from pySimBlocks.gui.blocks.port_meta import PortMeta


class FileSourceMeta(BlockMeta):

    def __init__(self):
        self.name = "FileSource"
        self.category = "sources"
        self.type = "file_source"
        self.summary = "Read a sequence of samples from a CSV, NPY, or NPZ file."
        self.description = (
            "Loads samples from file and outputs one sample per simulation step.\n\n"
            "- `file_type = npz`: reads one array from the archive (`key` mandatory).\n"
            "- `file_type = npy`: reads one array from a NPY file (`key` unused).\n"
            "- `file_type = csv`: reads one numeric CSV column (`key` = column name).\n\n"
            "Each step emits one row as a column vector."
        )

        self.parameters = [
            ParameterMeta(
                name="file_path",
                type="str",
                required=True,
                description="Path to the source file."
            ),
            ParameterMeta(
                name="file_type",
                type="enum",
                required=True,
                autofill=True,
                default="npz",
                enum=["npz", "npy", "csv"],
                description="Input file format."
            ),
            ParameterMeta(
                name="key",
                type="str",
                description="NPZ array key or CSV column name."
            ),
            ParameterMeta(
                name="repeat",
                type="enum",
                autofill=True,
                default=False,
                enum=[False, True],
                description="If true, replay samples from the beginning after end of file."
            ),
            ParameterMeta(
                name="sample_time",
                type="float",
                description="Block execution period."
            ),
        ]

        self.outputs = [
            PortMeta(
                name="out",
                display_as="out",
                shape=["n", 1],
                description="Current output sample."
            )
        ]

    def is_parameter_active(self, param_name: str, instance_values: Dict[str, Any]) -> bool:
        file_type = instance_values.get("file_type", "npz")

        if param_name == "key":
            return file_type in {"npz", "csv"}

        return super().is_parameter_active(param_name, instance_values)
