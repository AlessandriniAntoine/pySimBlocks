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

from typing import Dict, List

import numpy as np

from pySimBlocks.core.block import Block
from pySimBlocks.core.config import SimulationConfig
from pySimBlocks.core.fixed_time_manager import FixedStepTimeManager
from pySimBlocks.core.model import Model
from pySimBlocks.core.scheduler import Scheduler
from pySimBlocks.core.task import Task


class Simulator:
    """Discrete-time simulator with strict Simulink-like semantics.
 
    Each simulation step follows four phases:
 
    1. **output_update** — blocks compute y[k] from x[k] and u[k].
    2. **Propagate** — outputs are forwarded to downstream inputs.
    3. **state_update** — blocks compute x[k+1] from x[k] and u[k].
    4. **Commit** — x[k+1] is copied into x[k].
 
    This guarantees proper separation of outputs and state transitions,
    correct causal behavior for feedback loops, and algebraic loop
    detection through the model's topological ordering.
 
    Attributes:
        model: The block-diagram model to simulate.
        sim_cfg: Simulation execution configuration.
        verbose: If True, print step-by-step execution logs.
        logs: Logged signal values keyed by variable name.
    """

    def __init__(
        self,
        model: Model,
        sim_cfg: SimulationConfig,
        verbose: bool = False,
    ):
        """Initialize and compile the simulator.
 
        Args:
            model: The block-diagram model to simulate.
            sim_cfg: Simulation execution configuration.
            verbose: If True, print execution logs.
        """
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

    def initialize(self, t0: float = 0.0) -> None:
        """Initialize all blocks and propagate initial outputs.
 
        Args:
            t0: Initial simulation time in seconds.
 
        Raises:
            RuntimeError: If any block raises during initialization.
        """
        self.t = float(t0)
        self.t_step = float(t0)
        self.logs = {"time": []}
        self._log_shapes: Dict[str, tuple[int, int]] = {}

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

    def step(self, dt_override: float | None = None) -> None:
        """Perform one simulation step.
 
        With an internal clock, dt is provided by the time manager.
        With an external clock, dt_override must be supplied by the caller.
 
        Args:
            dt_override: Time step in seconds, required when using an
                external clock. Must not be provided for an internal clock.
 
        Raises:
            RuntimeError: If dt_override is missing for an external clock,
                or provided for an internal clock.
            ValueError: If dt_override is not strictly positive.
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

        # PHASE 3 — commit states
        for task in active_tasks:
            for block in task.state_blocks:
                block.commit_state()

        for task in active_tasks:
            task.advance()

        self.t_step = self.t
        self.t += dt_scheduler

    def run(
        self,
        T: float | None = None,
        t0: float | None = None,
        logging: list[str] | None = None,
        ) -> Dict[str, List[np.ndarray]]:
        """Run the simulation from t0 to T.
 
        Falls back to sim_cfg values for any argument not provided.
 
        Args:
            T: Simulation end time in seconds.
            t0: Simulation start time in seconds.
            logging: List of variable names to log (e.g.
                ``"BlockName.outputs.port"``).
 
        Returns:
            Dict mapping variable names to their logged values over time.
 
        Raises:
            RuntimeError: If called with an external clock configuration.
        """
        if self.sim_cfg.clock == "external":
            raise RuntimeError("Simulator.run() is not supported with external clock. Use step(dt_override=...)")

        sim_duration = T if T is not None else self.sim_cfg.T
        t0_run = t0 if t0 is not None else self.sim_cfg.t0
        logging_run = logging if logging is not None else self.sim_cfg.logging

        self.initialize(t0_run)

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

    def get_data(self,
                 variable: str | None = None,
                 block:str | None = None,
                 port: str | None = None) -> np.ndarray:
        """Retrieve logged data for a variable as a NumPy array.
 
        Provide either variable or the (block, port) pair:
 
        - ``variable``: full log key, e.g. ``"BlockName.outputs.port"``.
        - ``block`` + ``port``: shorthand for ``"block.outputs.port"``.
 
        Args:
            variable: Full variable name as logged.
            block: Block name (used with port).
            port: Output port name (used with block).
 
        Returns:
            Array of shape ``(n_steps, *signal_shape)`` containing the
            logged values.
 
        Raises:
            ValueError: If neither variable nor (block, port) is provided,
                if the variable is not found in logs, or if the log is empty
                or cannot be converted to a NumPy array.
        """
        if variable is not None:
            var_name = variable
        elif block is not None and port is not None:
            var_name = f"{block}.outputs.{port}"
        else:
            raise ValueError("Either variable or (block, port) must be provided.")

        if var_name not in self.logs:
            raise ValueError(f"Variable '{var_name}' is not logged. Available logs: {list(self.logs.keys())}")

        data = self.logs.get(var_name)
        if data is None:
            raise ValueError(f"No data found for variable '{var_name}'.")
        length = len(data)
        if length == 0:
            raise ValueError(f"Log for variable '{var_name}' is empty.")
        shape = data[0].shape
        try:
            data_array = np.array(data).reshape(length, *shape)
        except Exception as e:
            raise ValueError(f"Failed to convert log data for variable '{var_name}' to numpy array: {e}") from e

        return data_array

    # --------------------------------------------------------------------------
    # Private methods
    # --------------------------------------------------------------------------

    def _compile(self) -> None:
        """Prepare the simulator for execution.
 
        Builds execution order, groups blocks into tasks by sample time,
        and initializes the scheduler and time manager.
 
        Raises:
            NotImplementedError: If solver is ``"variable"``.
            ValueError: If solver is unknown.
        """
        self.output_order = self.model.build_execution_order()
        self.model.resolve_sample_times(self.sim_cfg.dt)
        self.model._rebuild_downstream_map()
        sample_times = [b._effective_sample_time for b in self.model.blocks.values()]

        tasks_by_ts = {}
        for b in self.model.blocks.values():
            sample_time = b._effective_sample_time
            tasks_by_ts.setdefault(sample_time, []).append(b)

        self.tasks = [
            Task(sample_time, blocks, self.output_order)
            for sample_time, blocks in tasks_by_ts.items()
        ]

        self._single_task = (len(self.tasks) == 1)
        if self._single_task:
            self._task0 = self.tasks[0]

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

    def _propagate_from(self, block: Block) -> None:
        """Forward outputs of block to its direct downstream inputs."""
        blocks = self.model.blocks
        for (src, dst) in self.model.downstream_of(block.name):
            _, src_port = src
            dst_block, dst_port = dst
            value = block.outputs[src_port]
            if value is not None:
                blocks[dst_block].inputs[dst_port] = value

    def _log(self, variables_to_log: List[str]) -> None:
        """Log specified variables at the current timestep.
 
        Raises:
            ValueError: If a variable format is invalid or the container
                is unknown.
            RuntimeError: If a logged value is None, not 2D, or changes
                shape across timesteps.
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
