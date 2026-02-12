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


class ChirpMeta(BlockMeta):

    def __init__(self):
        self.name = "Chirp"
        self.category = "sources"
        self.type = "chirp"
        self.summary = "Multi-dimensional chirp signal source (linear or logarithmic)."

        self.description = (
            "Generates a frequency-sweep (chirp) signal.\n\n"

            "Linear mode:\n"
            "$$\n"
            "\\phi_i(t) = 2\\pi\\left(f_{0,i}\\tau + "
            "\\tfrac{1}{2}k_i\\tau^2\\right) + \\varphi_i\n"
            "$$\n"
            "with:\n"
            "$$\n"
            "k_i = \\frac{f_{1,i} - f_{0,i}}{T_i}\n"
            "$$\n\n"

            "Logarithmic mode:\n"
            "$$\n"
            "\\phi_i(t) = "
            "\\frac{2\\pi f_{0,i} T_i}{\\ln(f_{1,i}/f_{0,i})}"
            "\\left[\\left(\\frac{f_{1,i}}{f_{0,i}}\\right)^{\\tau/T_i} - 1\\right]"
            " + \\varphi_i\n"
            "$$\n\n"

            "Output:\n"
            "$$\n"
            "y_i(t) = A_i \\sin(\\phi_i(t)) + o_i\n"
            "$$\n\n"

            "with:\n"
            "$$\n"
            "\\tau = \\max(0, t - t_{0,i})\n"
            "$$\n"
        )

        self.parameters = [

            ParameterMeta(
                name="amplitude",
                type="scalar | vector | matrix",
                required=True,
                autofill=True,
                default=[[1.0]],
                description="Chirp amplitude."
            ),

            ParameterMeta(
                name="f0",
                type="scalar | vector | matrix",
                required=True,
                autofill=True,
                default=[[1.0]],
                description="Start frequency in Hertz."
            ),

            ParameterMeta(
                name="f1",
                type="scalar | vector | matrix",
                required=True,
                autofill=True,
                default=[[10.0]],
                description="End frequency in Hertz."
            ),

            ParameterMeta(
                name="duration",
                type="scalar | vector | matrix",
                required=True,
                autofill=True,
                default=[[5.0]],
                description="Frequency sweep duration in seconds."
            ),

            ParameterMeta(
                name="mode",
                type="enum",
                required=True,
                autofill=True,
                default="linear",
                enum=["linear", "log"],
                description="Sweep mode: 'linear' or 'log'."
            ),

            ParameterMeta(
                name="start_time",
                type="scalar | vector | matrix",
                description="Time at which the chirp starts."
            ),

            ParameterMeta(
                name="phase",
                type="scalar | vector | matrix",
                description="Initial phase in radians."
            ),

            ParameterMeta(
                name="offset",
                type="scalar | vector | matrix",
                description="Constant offset added to the signal."
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
                description="Chirp output signal."
            )
        ]
