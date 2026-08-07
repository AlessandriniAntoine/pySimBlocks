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


class TransferFunctionMeta(BlockMeta):
    """Describe the GUI metadata of the SISO transfer-function block."""

    def __init__(self):
        """Initialize transfer-function block metadata.

        Args:
            None.

        Raises:
            None.
        """
        self.name = "TransferFunction"
        self.category = "systems"
        self.type = "transfer_function"
        self.summary = "SISO transfer function H(s) or H(z), executed as a discrete state-space system."
        self.description = (
            "Realizes a SISO transfer function:\n"
            "$$\n"
            "H(s) = \\frac{num(s)}{den(s)} \\quad \\text{or} \\quad H(z) = \\frac{num(z)}{den(z)}\n"
            "$$\n"
            "num/den are coefficient lists in decreasing powers, "
            "e.g. for (2s + 3) / (s^2 + 4s + 5): num=[2, 3], den=[1, 4, 5].\n"
            "When domain is 'continuous', the system is discretized using sample_time "
            "(or the global simulation dt if omitted).\n"
        )

        self.parameters = [
            ParameterMeta(
                name="num",
                type="vector",
                required=True,
                autofill=True,
                default=[1.0],
                description="Numerator coefficients, highest power first."
            ),
            ParameterMeta(
                name="den",
                type="vector",
                required=True,
                autofill=True,
                default=[1.0, -0.9],
                description="Denominator coefficients, highest power first."
            ),
            ParameterMeta(
                name="domain",
                type="enum",
                required=True,
                autofill=True,
                default="discrete",
                enum=["discrete", "continuous"],
                description="Domain of num/den: polynomials in z (discrete) or s (continuous)."
            ),
            ParameterMeta(
                name="discretization",
                type="enum",
                default="tustin",
                enum=["tustin", "zoh"],
                description="Discretization method, used only when domain is 'continuous'. "
                             "'zoh' requires scipy."
            ),
            ParameterMeta(
                name="x0",
                type="vector",
                description="Initial state vector."
            ),
            ParameterMeta(
                name="sample_time",
                type="float",
                description="Block execution period. If omitted, the global simulation "
                             "dt is used, even when domain is 'continuous'."
            )
        ]

        self.inputs = [
            PortMeta(
                name="u",
                display_as="u",
                shape=[1, 1],
                description="Input signal."
            )
        ]

        self.outputs = [
            PortMeta(
                name="x",
                display_as="x",
                shape=["n", 1],
                description="State vector."
            ),
            PortMeta(
                name="y",
                display_as="y",
                shape=[1, 1],
                description="Output signal."
            )
        ]
