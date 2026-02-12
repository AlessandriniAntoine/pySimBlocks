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


class WhiteNoiseMeta(BlockMeta):

    def __init__(self):
        self.name = "WhiteNoise"
        self.category = "sources"
        self.type = "white_noise"
        self.summary = "Multi-dimensional Gaussian white noise source."
        self.description = (
            "Generates independent Gaussian noise samples at each simulation step:\n"
            "$$\n"
            "y_i(t) \\sim \\mathcal{N}(\\mu_i, \\sigma_i^2)\n"
            "$$\n"
        )

        self.parameters = [
            ParameterMeta(
                name="mean",
                type="scalar | vector | matrix",
                description="Mean value of the noise."
            ),
            ParameterMeta(
                name="std",
                type="scalar | vector | matrix",
                description="Standard deviation of the noise."
            ),
            ParameterMeta(
                name="seed",
                type="int",
                description="Random seed for reproducibility."
            ),
            ParameterMeta(
                name="sample_time",
                type="float",
                description="Block execution period."
            )
        ]

        self.outputs = [
            PortMeta(
                name="out",
                display_as="out",
                shape=["n", "m"],
                description="Gaussian noise output signal."
            )
        ]
