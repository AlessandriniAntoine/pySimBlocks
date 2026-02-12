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


class RateLimiterMeta(BlockMeta):

    def __init__(self):
        self.name = "RateLimiter"
        self.category = "operators"
        self.type = "rate_limiter"
        self.summary = "Discrete-time rate limiter block."
        self.description = (
            "Limits the rate of change of the output signal according to:\n"
            "$$\n"
            "\\Delta u = u[k] - y[k-1]\n"
            "$$\n"
            "$$\n"
            "y[k] = y[k-1] + \\mathrm{clip}(\\Delta u,\\; s^{-} dt,\\; s^{+} dt)\n"
            "$$\n"
            "where $s^{+}$ is the rising slope and $s^{-}$ is the falling slope."
        )

        self.parameters = [
            ParameterMeta(
                name="rising_slope",
                type="scalar | vector | matrix"
            ),
            ParameterMeta(
                name="falling_slope",
                type="scalar | vector | matrix"
            ),
            ParameterMeta(
                name="initial_output",
                type="scalar | vector | matrix"
            ),
            ParameterMeta(
                name="sample_time",
                type="float"
            )
        ]

        self.inputs = [
            PortMeta(
                name="in",
                display_as="in",
                shape=["n", "m"],
                description="Input signal."
            )
        ]

        self.outputs = [
            PortMeta(
                name="out",
                display_as="out",
                shape=["n", "m"],
                description="Rate-limited output signal."
            )
        ]
