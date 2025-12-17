from typing import Dict, List
import numpy as np

from pySimBlocks.core.config import SimulationConfig
from pySimBlocks.core.model import Model
from pySimBlocks.core.fixed_time_manager import FixedStepTimeManager
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

    # ----------------------------------------------------------------------
    # COMPILE
    # ----------------------------------------------------------------------
    def _compile(self):
        self.output_order = self.model.build_execution_order()
        self.model.resolve_sample_times(self.sim_cfg.dt)
        sample_times = [b._effective_sample_time for b in self.model.blocks.values()]

        # regroup blocks by sample time
        tasks_by_ts = {}
        for b in self.model.blocks.values():
            Ts = b._effective_sample_time
            tasks_by_ts.setdefault(Ts, []).append(b)

        self.tasks = [
            Task(Ts, blocks, self.output_order)
            for Ts, blocks in tasks_by_ts.items()
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

    # ----------------------------------------------------------------------
    # INITIALIZATION
    # ----------------------------------------------------------------------
    def initialize(self, t0: float = 0.0):
        self.t = float(t0)
        self.t_step = float(t0)
        self.logs = {"time": []}

        # Initialisation bloc par bloc + propagation
        for block in self.output_order:
            try:
                block.initialize(self.t)
                self._propagate_from(block)
            except Exception as e:
                raise RuntimeError(
                    f"Error during initialization of block '{block.name}': {e}"
                ) from e


    # ----------------------------------------------------------------------
    # PROPAGATION
    # ----------------------------------------------------------------------
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

    # ----------------------------------------------------------------------
    # LOG
    # ----------------------------------------------------------------------
    def _log(self, variables_to_log):
        for var in variables_to_log:
            block_name, container, key = var.split(".")
            block = self.model.blocks[block_name]

            if container == "outputs":
                value = block.outputs[key]
            elif container == "state":
                value = block.state[key]
            else:
                raise ValueError(f"Unknown container '{container}' in '{var}'.")

            if var not in self.logs:
                self.logs[var] = []
            self.logs[var].append(np.copy(value))

        self.logs["time"].append(np.array([self.t_step]))

    # ----------------------------------------------------------------------
    # ONE SIMULATION STEP
    # ----------------------------------------------------------------------
    def step(self):

        dt_scheduler = self.time_manager.next_dt(self.t)
        active_tasks = self.scheduler.active_tasks(self.t)

        print(f"time: {self.t}; dt: {dt_scheduler}, active_tasks: {active_tasks}")

        # PHASE 1 — outputs
        for task in active_tasks:
            dt_task = task.get_dt(self.t)
            for block in task.output_blocks:
                print(f"\tBlock: {block.name} with dt: {dt_task}")
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


    # ----------------------------------------------------------------------
    # RUN MULTIPLE STEPS
    # ----------------------------------------------------------------------
    def run(
        self,
        T: float | None = None,
        t0: float | None = None,
        logging: list[str] | None = None,
    ):
        T_run = T if T is not None else self.sim_cfg.T
        t0_run = t0 if t0 is not None else self.sim_cfg.t0
        logging_run = logging if logging is not None else self.sim_cfg.logging

        self.initialize(t0_run)

        # Main loop
        while self.t <= T_run +0.3*self.sim_cfg.dt: # do one more iteration as t is updated at the end of step
            self.step()
            self._log(logging_run)

            if self.verbose:
                print(f"\nTime: {self.t_step}/{T_run}")
                for variable in logging_run:
                    print(f"{variable}: {self.logs[variable][-1]}")



        for block in self.model.blocks.values():
            try:
                block.finalize()
            except Exception as e:
                print(f"[WARNING] finalize() failed for block {block.name}: {e}")


        return self.logs
