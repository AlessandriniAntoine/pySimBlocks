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

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from pySimBlocks.core.block import Block


class SofaExchangeIO(Block):
    """SOFA exchange interface block.

    Acts as a data exchange boundary between a pySimBlocks model and an
    external SOFA controller. Input and output ports are declared dynamically
    from ``input_keys`` and ``output_keys``. The block is stateless and
    performs no computation — outputs are produced by upstream blocks in the
    pySimBlocks model through normal signal propagation.

    Attributes:
        input_keys: Names of the input ports fed by the SOFA controller.
        output_keys: Names of the output ports consumed by the SOFA controller.
        slider_params: Optional ImGui slider configuration, mapping
            ``"BlockName.attr"`` to ``[min, max]`` bounds.
    """

    direct_feedthrough = False
    is_source = False

    def __init__(
        self,
        name: str,
        input_keys: list[str],
        output_keys: list[str],
        slider_params: Dict[str, List[float]] | None = None,
        sample_time: float | None = None,
    ):
        """Initialize a SofaExchangeIO block.

        Args:
            name: Unique identifier for this block instance.
            input_keys: Names of the input ports.
            output_keys: Names of the output ports.
            slider_params: Optional ImGui slider configuration mapping
                ``"BlockName.attr"`` to ``[min, max]`` bounds. None to
                disable sliders.
            sample_time: Sampling period in seconds, or None to use the
                global simulation dt.
        """
        super().__init__(name, sample_time)

        self.input_keys = input_keys
        self.output_keys = output_keys
        self.slider_params = slider_params

        for k in input_keys:
            self.inputs[k] = None
        for k in output_keys:
            self.outputs[k] = None


    # --------------------------------------------------------------------------
    # Class methods
    # --------------------------------------------------------------------------

    @classmethod
    def adapt_params(
        cls,
        params: Dict[str, Any],
        params_dir: Path | None = None,
    ) -> Dict[str, Any]:
        """Strip the ``scene_file`` key which is not used by this block.

        Args:
            params: Raw parameter dict loaded from the YAML project file.
            params_dir: Directory of the project file. Not used here.

        Returns:
            Parameter dict with ``scene_file`` removed.
        """
        adapted = dict(params)
        adapted.pop("scene_file", None)
        return adapted


    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------

    def initialize(self, t0: float) -> None:
        """No-op: ports are already declared in __init__."""

    def output_update(self, t: float, dt: float) -> None:
        """Verify that all inputs are present; outputs are set by upstream blocks.

        Args:
            t: Current simulation time in seconds.
            dt: Current time step in seconds.

        Raises:
            RuntimeError: If any expected input port is None.
        """
        for k in self.input_keys:
            if self.inputs[k] is None:
                raise RuntimeError(f"[{self.name}] Missing input '{k}' at time {t}.")

    def state_update(self, t: float, dt: float) -> None:
        """No-op: SofaExchangeIO carries no internal state."""
