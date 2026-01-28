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

from typing import Dict, List

import numpy as np

from pySimBlocks.core.config import SimulationConfig
from pySimBlocks.core.fixed_time_manager import FixedStepTimeManager
from pySimBlocks.core.model import Model
from pySimBlocks.core.scheduler import Scheduler
from pySimBlocks.core.task import Task


class Simulator:
    """
    Discrete-time simulator with strict Simulink-like semantics:

        For each step k:

          1) PHASE 1: output_update(t)
             Blocks compute outputs y[k] from x[k] and u[k].

          2) Propagate all outputs to downstream inputs.

          3) PHASE 2: state_update(t, dt)
             Blocks compute x[k+1] from x[k] and u[k].

          4) Commit x[k+1] -> x[k].

    This guarantees:
        - Proper separation of outputs and state transitions.
        - Correct causal behavior for feedback loops.
        - Algebraic loop detection through the Model's topo ordering.
    """

    def __init__(
        self,
        model: Model,
        sim_cfg: SimulationConfig,
        verbose: bool = False,
    ):

        self.model = model
        self.sim_cfg = sim_cfg
        self.verbose = verbose
        self.model.verbose = verbose

        self.sim_cfg.validate()
        self._compile()

        self.logs: Dict[str, List[np.ndarray]] = {"time": []}


    # --------------------------------------------------------------------------
    # Public methods
    # --------------------------------------------------------------------------
    def initialize(self, t0: float = 0.0):
        """Initialize all blocks and propagate initial outputs."""
        self.t = float(t0)
        self.t_step = float(t0)
        self.logs = {"time": []}
        self._log_shapes: Dict[str, tuple[int, int]] = {}

        # Initialisation bloc par bloc + propagation
        for block in self.output_order:
            try:
                block.initialize(self.t)
                self._propagate_from(block)
            except Exception as e:
                raise RuntimeError(
                    f"Error during initialization of block '{block.name}': {e}"
                ) from e
        for task in self.tasks:
            task.update_state_blocks()

    # ------------------------------------------------------------------
    def step(self, dt_override: float | None = None) -> None:
        """
        Perform one simulation step.

        If dt_override is provided, the simulator time advance is driven by this
        external dt (real-time clock). Otherwise, dt is provided by the internal
        time manager (fixed-step).
        """
        # 0) Choose dt for this tick
        if self.sim_cfg.clock == "external":
            if dt_override is None:
                raise RuntimeError(
                    "[Simulator] dt_override must be provided when using external clock."
                )
            else:
                dt_scheduler = float(dt_override)
                if dt_scheduler <= 0.0:
                    raise ValueError(f"[Simulator] dt_override must be > 0. Got {dt_scheduler}")
        else:  # internal clock
            if dt_override is not None:
                raise RuntimeError(
                    "[Simulator] dt_override should not be provided when using internal clock."
                )
            dt_scheduler = self.time_manager.next_dt(self.t)

        active_tasks = self.scheduler.active_tasks(self.t)

        # PHASE 1 — outputs
        for task in active_tasks:
            dt_task = task.get_dt(self.t)
            for block in task.output_blocks:
                block.output_update(self.t, dt_task)
                self._propagate_from(block)

        # PHASE 2 — states
        for task in active_tasks:
            dt_task = task.get_dt(self.t)
            for block in task.state_blocks:
                block.state_update(self.t, dt_task)

        for task in active_tasks:
            for block in task.state_blocks:
                block.commit_state()

        for task in active_tasks:
            task.advance()

        self.t_step = self.t
        self.t += dt_scheduler

    # ------------------------------------------------------------------
    def run(
        self,
        T: float | None = None,
        t0: float | None = None,
        logging: list[str] | None = None,
    ):
        """Run the simulation from t0 to T.
        If T, t0 or logging are not provided, use the simulator's config.
        Returns:
            logs (Dict[str, List[np.ndarray]]): Logged variables over time.
        """
        if self.sim_cfg.clock == "external":
            raise RuntimeError("Simulator.run() is not supported with external clock. Use step(dt_override=...)")

        sim_duration = T if T is not None else self.sim_cfg.T
        t0_run = t0 if t0 is not None else self.sim_cfg.t0
        logging_run = logging if logging is not None else self.sim_cfg.logging

        self.initialize(t0_run)

        # Main loop (with a small epsilon to avoid floating-point issues)
        eps = 1e-12
        while self.t_step < sim_duration - eps:
            self.step()
            self._log(logging_run)

            if self.verbose:
                print(f"\nTime: {self.t_step}/{sim_duration}")
                for variable in logging_run:
                    print(f"{variable}: {self.logs[variable][-1]}")



        for block in self.model.blocks.values():
            try:
                block.finalize()
            except Exception as e:
                print(f"[WARNING] finalize() failed for block {block.name}: {e}")


        return self.logs


    # --------------------------------------------------------------------------
    # Private methods
    # --------------------------------------------------------------------------
    def _compile(self):
        """Prepare the simulator for execution.
        - Build execution order.
        - Group blocks into tasks by sample time.
        - Initialize the scheduler and time manager.
        """
        self.output_order = self.model.build_execution_order()
        self.model.resolve_sample_times(self.sim_cfg.dt)
        sample_times = [b._effective_sample_time for b in self.model.blocks.values()]

        # regroup blocks by sample time
        tasks_by_ts = {}
        for b in self.model.blocks.values():
            sample_time = b._effective_sample_time
            tasks_by_ts.setdefault(sample_time, []).append(b)

        self.tasks = [
            Task(sample_time, blocks, self.output_order)
            for sample_time, blocks in tasks_by_ts.items()
        ]

        self.scheduler = Scheduler(self.tasks)

        if self.sim_cfg.solver == "fixed":
            self.time_manager = FixedStepTimeManager(
                dt_base=self.sim_cfg.dt,
                sample_times=list(set(sample_times))
            )
        elif self.sim_cfg.solver == "variable":
            raise NotImplementedError(
                "Variable-step simulation is not implemented yet."
            )
        else:
            raise ValueError(
                f"Unknown simulation mode '{self.sim_cfg.solver}'. "
                "Supported modes are: 'fixed', 'variable'."
            )

    # ------------------------------------------------------------------
    def _propagate_from(self, block):
        """
        Propagate outputs of `block` to its direct downstream blocks.
        """
        for (src, dst) in self.model.downstream_of(block.name):
            src_block, src_port = src
            dst_block, dst_port = dst

            value = self.model.blocks[src_block].outputs[src_port]
            if value is not None:
                self.model.blocks[dst_block].inputs[dst_port] = value

    # ------------------------------------------------------------------
    def _log(self, variables_to_log):
        """Log specified variables at the current time step.

        Enforces:
            - logged values must be 2D numpy arrays
            - shape must stay constant over time for each logged variable
        """
        for var in variables_to_log:
            block_name, container, key = var.split(".")
            block = self.model.blocks[block_name]

            if container == "outputs":
                value = block.outputs[key]
            elif container == "state":
                value = block.state[key]
            else:
                raise ValueError(f"Unknown container '{container}' in '{var}'.")

            if value is None:
                raise RuntimeError(
                    f"[Simulator] Cannot log '{var}' at t={self.t_step}: value is None."
                )

            arr = np.asarray(value)

            if arr.ndim != 2:
                raise RuntimeError(
                    f"[Simulator] Cannot log '{var}' at t={self.t_step}: expected a 2D array, "
                    f"got ndim={arr.ndim} with shape {arr.shape}."
                )

            # Enforce constant shape over time for this variable
            if var not in self._log_shapes:
                self._log_shapes[var] = arr.shape
            else:
                expected_shape = self._log_shapes[var]
                if arr.shape != expected_shape:
                    raise RuntimeError(
                        f"[Simulator] Logged signal '{var}' changed shape over time at t={self.t_step}: "
                        f"expected {expected_shape}, got {arr.shape}."
                    )

            if var not in self.logs:
                self.logs[var] = []
            self.logs[var].append(np.copy(arr))

        self.logs["time"].append(np.array([self.t_step]))
