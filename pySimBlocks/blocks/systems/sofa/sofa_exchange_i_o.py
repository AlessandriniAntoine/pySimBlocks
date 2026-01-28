# ******************************************************************************
#                                  pySimBlocks
#                     Copyright (c) 2026 Antoine Alessandrini
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

from pathlib import Path
from typing import Any, Dict, List
from pySimBlocks.core.block import Block


class SofaExchangeIO(Block):
    """
    SOFA exchange interface block.

    Summary:
        Provides an interface between a pySimBlocks model and an external
        SOFA controller by exposing dynamic input and output ports.

    Parameters (overview):
        input_keys : list of str
            Names of externally provided input signals.
        output_keys : list of str
            Names of output signals to be consumed by SOFA.
        scene_file : str
            Path to the SOFA scene file, used only for automatic generation.
        sample_time : float, optional
            Block execution period.

    I/O:
        Inputs:
            Defined dynamically by input_keys.
        Outputs:
            Defined dynamically by output_keys.

    Notes:
        - This block does not run a SOFA simulation.
        - It acts only as a data exchange interface.
        - The block is stateless.
        - Outputs are produced by the pySimBlocks controller logic.
    """


    direct_feedthrough = False
    is_source = False

    def __init__(self,
            name: str,
            input_keys: list[str],
            output_keys: list[str],
            slider_params: Dict[str, List[float]] | None = None,
            sample_time: float | None = None
        ):
        super().__init__(name, sample_time)

        self.input_keys = input_keys
        self.output_keys = output_keys
        self.slider_params = slider_params

        # Declare dynamic ports
        for k in input_keys:
            self.inputs[k] = None
        for k in output_keys:
            self.outputs[k] = None


    # --------------------------------------------------------------------------
    # Class Methods
    # --------------------------------------------------------------------------
    @classmethod
    def adapt_params(cls, 
                     params: Dict[str, Any], 
                     params_dir: Path | None = None) -> Dict[str, Any]:
        """
        Adapt parameters from yaml format to class constructor format.
        Adapt function file and name in a yaml format into callable.
        """
        adapted = dict(params)
        adapted.pop("scene_file", None)
        return adapted


    # --------------------------------------------------------------------------
    # Public Methods
    # --------------------------------------------------------------------------
    def initialize(self, t0: float):
        pass

    # ------------------------------------------------------------------
    def output_update(self, t: float, dt: float):
        """
        Outputs are produced by upstream blocks (controller).
        This block itself does nothing but check validity.
        """
        # Ensure inputs exist
        for k in self.input_keys:
            if self.inputs[k] is None:
                raise RuntimeError(f"[{self.name}] Missing input '{k}' at time {t}.")

        # Outputs are set by other blocks (controller chain) through normal propagation.
        pass

    # ------------------------------------------------------------------
    def state_update(self, t: float, dt: float):
        # Stateless block: no internal state
        pass
