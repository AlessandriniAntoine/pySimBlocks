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

import time
import numpy as np
from typing import Any, Dict, List, Optional
from pySimBlocks.core.simulator import Simulator


class RealTimeRunner:
    """Run a simulator step loop against a real-time clock.

    The runner measures or accepts an external timestep, forwards input values
    to model blocks, advances the simulator, and collects output values.

    Attributes:
        sim: Simulator instance driven by the runner.
        input_blocks: Model blocks updated from external inputs at each tick.
        output_blocks: Model blocks read to produce external outputs.
        target_dt: Optional target period used for pacing.
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
        """Initialize the real-time runner.

        Args:
            sim: Initialized simulator instance with a compiled model.
            input_blocks: Names of model blocks that receive external inputs.
            output_blocks: Names of model blocks that expose external outputs.
            target_dt: Target loop period in seconds for optional pacing.
            time_source: Clock source name, either ``"perf_counter"`` or
                ``"time"``.

        Raises:
            ValueError: If ``time_source`` is not supported.
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


    # --- Public methods ---

    def initialize(self, t0: float = 0.0) -> None:
        """Initialize the simulator and synchronize the runner clock.

        Args:
            t0: Initial simulation time in seconds.
        """
        self.sim.initialize(t0)
        self._t_prev = self._now()

    def tick(
        self,
        inputs: Dict[str, Any],
        *,
        dt: Optional[float] = None,
        pace: bool = False,
    ) -> Dict[str, np.ndarray]:
        """Execute one real-time simulation tick.

        Args:
            inputs: External input values keyed by block name.
            dt: Explicit timestep override in seconds. If omitted, the runner
                measures elapsed wall-clock time.
            pace: If True, sleep after the step to approximate ``target_dt``.

        Returns:
            Output values keyed by block name as column vectors.

        Raises:
            KeyError: If a required input block value is missing.
            RuntimeError: If an output block does not provide an ``"out"``
                value.
        """
        if self._t_prev is None:
            self._t_prev = self._now()

        t_now = self._now()
        dt_meas = t_now - self._t_prev
        dt_used = float(dt) if dt is not None else float(dt_meas)

        # warning if dt is much larger than target_dt
        if self.target_dt is not None and dt_used > 1.5 * self.target_dt:
            print(f"[RealTimeRunner] Warning: dt={dt_used:.3f}s exceeds target_dt={self.target_dt:.3f}s")

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
