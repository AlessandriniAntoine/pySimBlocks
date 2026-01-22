# ******************************************************************************
#                                 pySimBlocks                                 
#                Copyright (c) 2026 The pySimBlocks Authors               
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

import time
import numpy as np
from typing import Any, Dict, List, Optional
from pySimBlocks.core.simulator import Simulator


class RealTimeRunner:
    """
    Generic real-time runner for pySimBlocks.

    Responsibilities:
      - Provide an external clock (dt measured or provided).
      - Push external inputs into ExternalInput blocks.
      - Call Simulator.step(dt_override=...).
      - Pull outputs from ExternalOutput blocks.

    Notes:
      - No threading, no I/O drivers here. The application owns that.
      - Designed to be embedded in user-specific real-time apps.
    """

    def __init__(
        self,
        sim: Simulator,
        input_blocks: List[str],
        output_blocks: List[str],
        *,
        target_dt: Optional[float] = None,
        time_source: str = "perf_counter",  # "perf_counter" | "time"
    ):
        """
        Parameters
        ----------
        sim:
            Initialized Simulator instance (model already compiled).
        input_blocks:
            Mapping external input name -> block name in model
            Example: {"camera": "Camera", "ref": "Reference"}
        output_blocks:
            Mapping external output name -> block name in model
            Example: {"motor": "Motor"}
        target_dt:
            If provided, runner will pace the loop to approximately this period
            (best effort). If None, no pacing.
        time_source:
            Timer function selection.
        """
        self.sim = sim
        self.input_blocks = {block_name: sim.model.get_block_by_name(block_name) for block_name in input_blocks}
        self.output_blocks = {block_name: sim.model.get_block_by_name(block_name) for block_name in output_blocks}
        self.target_dt = target_dt

        if time_source == "perf_counter":
            self._now = time.perf_counter
        elif time_source == "time":
            self._now = time.time
        else:
            raise ValueError("time_source must be 'perf_counter' or 'time'")

        self._t_prev: Optional[float] = None

    def initialize(self, t0: float = 0.0) -> None:
        self.sim.initialize(t0)
        self._t_prev = self._now()

    def tick(
        self,
        inputs: Dict[str, Any],
        *,
        dt: Optional[float] = None,
        pace: bool = False,
    ) -> Dict[str, np.ndarray]:
        """
        Execute one real-time tick.

        Parameters
        ----------
        inputs:
            External inputs keyed by input_blocks mapping key.
            Example: {"camera": markers_pos, "ref": ref_value}
        dt:
            Optional explicit dt_override. If None, dt is measured from wall clock.
        pace:
            If True and target_dt is set, sleep to approximate target period.

        Returns
        -------
        outputs:
            Dict mapping output key -> np.ndarray (n,1)
        """
        if self._t_prev is None:
            self._t_prev = self._now()

        t_now = self._now()
        dt_meas = t_now - self._t_prev
        dt_used = float(dt) if dt is not None else float(dt_meas)

        # 1) push inputs
        for block_name, block in self.input_blocks.items():
            if block_name not in inputs:
                raise KeyError(f"[RealTimeRunner] Missing input '{block_name}'")
            block.inputs["in"] = inputs[block_name]

        # 2) step with external dt
        self.sim.step(dt_override=dt_used)

        # 3) pull outputs
        outputs: Dict[str, np.ndarray] = {}
        for block_name, block in self.output_blocks.items():
            y = block.outputs["out"]
            if y is None:
                raise RuntimeError(f"[RealTimeRunner] Output 'out' of block '{block_name}' is None")
            outputs[block_name] = np.asarray(y, dtype=float).reshape(-1, 1)

        # 4) bookkeeping + pacing
        self._t_prev = t_now

        if pace and self.target_dt is not None:
            elapsed = self._now() - t_now
            sleep_time = self.target_dt - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

        return outputs
