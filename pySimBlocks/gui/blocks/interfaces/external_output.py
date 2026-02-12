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

from pySimBlocks.gui.blocks.block_meta import BlockMeta
from pySimBlocks.gui.blocks.parameter_meta import ParameterMeta
from pySimBlocks.gui.blocks.port_meta import PortMeta


class ExternalOutputMeta(BlockMeta):

    def __init__(self):
        self.name = "ExternalOutput"
        self.category = "interfaces"
        self.type = "external_output"
        self.summary = "Pass-through block for external real-time commands/values."
        self.description = (
            "Pass-through block intended to expose a model command/value to an\n"
            "external real-time application (motors, network, hardware driver, etc.).\n\n"
            "This block does not perform any synchronization. It only enforces the\n"
            "pySimBlocks signal convention (column vectors of shape (n,1))."
        )

        self.parameters = [
            ParameterMeta(
                name="sample_time",
                type="float"
            )
        ]

        self.inputs = [
            PortMeta(
                name="in",
                display_as="in",
                shape=["n", 1],
                description="Model command/value signal."
            )
        ]

        self.outputs = [
            PortMeta(
                name="out",
                display_as="out",
                shape=["m", 1],
                description="External output signal."
            )
        ]
