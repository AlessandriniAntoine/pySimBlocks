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


class PIDMeta(BlockMeta):

    def __init__(self):
        self.name = "PID"
        self.category = "controllers"
        self.type = "pid"
        self.summary = "Discrete SISO PID controller."
        self.description = (
            "$$\n"
            "u[k] = K_p e[k] + K_i x_i[k] + K_d \frac{e[k]-e[k-1]}{dt}\n"
            "$$\n"
        )

        self.parameters = [
            ParameterMeta(
                name="controller",
                type="enum",
                required=True,
                autofill=True,
                default="PID",
                enum=["P", "I", "PI", "PD", "PID"]
            ),
            ParameterMeta(
                name="Kp",
                type="scalar",
                autofill=True,
                default=1.0,
                description="Proportionnal gain."
            ),
            ParameterMeta(
                name="Ki",
                type="scalar",
                default=1.0,
                description="Integral gain."
            ),
            ParameterMeta(
                name="Kd",
                type="scalar",
                default=1.0,
                description="Derivative gain."
            ),
            ParameterMeta(
                name="integration_method",
                type="enum",
                default="euler forward",
                enum=["euler forward", "euler backward"]
            ),
            ParameterMeta(
                name="u_min",
                type="scalar"
            ),
            ParameterMeta(
                name="u_max",
                type="scalar"
            ),
            ParameterMeta(
                name="sample_time",
                type="float"
            )
        ]

        self.inputs = [
            PortMeta(
                name="e",
                display_as="e",
                shape=[1, 1],
                description="Error signal."
            )
        ]

        self.outputs = [
            PortMeta(
                name="u",
                display_as="u",
                shape=[1, 1],
                description="Control command."
            )
        ]

    def is_parameter_active(self, param_name: str, instance_values: Dict[str, Any]) -> bool:

        if param_name == "Kp":
            return instance_values["controller"] in ["P", "PI", "PD", "PID"]
        elif param_name == "Ki":
            return instance_values["controller"] in ["I", "PI", "PID"]
        elif param_name == "Kd":
            return instance_values["controller"] in ["PD", "PID"]

        return super().is_parameter_active(param_name, instance_values)
