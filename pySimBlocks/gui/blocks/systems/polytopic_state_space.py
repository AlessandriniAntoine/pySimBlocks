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


class PolytopicStateSpaceMeta(BlockMeta):

    def __init__(self):
        self.name = "PolytopicStateSpace"
        self.category = "systems"
        self.type = "polytopic_state_space"
        self.summary = "Discrete-time polytopic state-space system."
        self.description = (
            "Implements the discrete-time polytopic state-space equations:\n"
            "$$\n"
            "x[k+1] = A\\,\\mathrm{kron}(w[k], x[k]) + B\\,\\mathrm{kron}(w[k], u[k])\n"
            "$$\n"
            "$$\n"
            "y[k] = C x[k]\n"
            "$$\n"
            "with $w[k]$ the vertex weight vector.\n"
        )

        self.parameters = [
            ParameterMeta(
                name="A",
                type="matrix",
                required=True,
                autofill=True,
                default=[[1.0, 0.0]],
                description="Stacked polytopic state matrix of shape (nx, r*nx): [A1 ... Ar]."
            ),
            ParameterMeta(
                name="B",
                type="matrix",
                required=True,
                autofill=True,
                default=[[1.0, 1.0]],
                description="Stacked polytopic input matrix of shape (nx, r*nu): [B1 ... Br]."
            ),
            ParameterMeta(
                name="C",
                type="matrix",
                required=True,
                autofill=True,
                default=[[1.0]],
                description="Output matrix of shape (ny, nx)."
            ),
            ParameterMeta(
                name="x0",
                type="vector",
                description="Initial state vector."
            ),
            ParameterMeta(
                name="sample_time",
                type="float",
                description="Block execution period."
            )
        ]

        self.inputs = [
            PortMeta(
                name="w",
                display_as="w",
                shape=["r", 1],
                description="Vertex weights vector."
            ),
            PortMeta(
                name="u",
                display_as="u",
                shape=["nu", 1],
                description="Input vector."
            )
        ]

        self.outputs = [
            PortMeta(
                name="x",
                display_as="x",
                shape=["nx", 1],
                description="State vector."
            ),
            PortMeta(
                name="y",
                display_as="y",
                shape=["ny", 1],
                description="Output vector."
            )
        ]
