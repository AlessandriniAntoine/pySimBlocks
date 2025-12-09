from typing import Dict, List
import numpy as np

from pySimBlocks.core.model import Model
from pySimBlocks.core.block import Block


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

    def __init__(self, model: Model, dt: float, verbose: bool = False):
        self.model = model
        self.dt = float(dt)
        self.t = 0.0
        self.verbose = verbose
        self.model.verbose = verbose

        # blocks in valid causal order
        self.output_order, self.state_order = model.build_execution_order()

        # logs: dict[var_name -> list[np.ndarray]]
        self.logs: Dict[str, List[np.ndarray]] = {"time": []}

    # ----------------------------------------------------------------------
    # INITIALIZATION
    # ----------------------------------------------------------------------
    def initialize(self, t0: float = 0.0):
        self.t = float(t0)

        # Initialisation bloc par bloc + propagation
        for block in self.output_order:
            try:
                block.initialize(self.t)
                self._propagate_all()
            except Exception as e:
                raise RuntimeError(
                    f"Error during initialization of block '{block.name}': {e}"
                ) from e


    # ----------------------------------------------------------------------
    # PROPAGATION
    # ----------------------------------------------------------------------
    def _propagate_all(self):
        """
        Propagate all outputs to downstream inputs (like Simulink)
        """
        for block in self.output_order:
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

        self.logs["time"].append(np.array([self.t - self.dt]))

    # ----------------------------------------------------------------------
    # ONE SIMULATION STEP
    # ----------------------------------------------------------------------
    def step(self):
        # -------------------------
        # PHASE 1: OUTPUT UPDATE
        # -------------------------
        for block in self.output_order:
            block.output_update(self.t)
            self._propagate_all()

        # -------------------------
        # PHASE 2: STATE UPDATE
        # -------------------------
        for block in self.state_order:
            block.state_update(self.t, self.dt)

        # -------------------------
        # COMMIT
        # -------------------------
        for block in self.state_order:
            block.commit_state()

        self.t += self.dt

    # ----------------------------------------------------------------------
    # RUN MULTIPLE STEPS
    # ----------------------------------------------------------------------
    def run(self, T: float, variables_to_log=None):
        if variables_to_log is None:
            variables_to_log = []

        N = int(round(T / self.dt))

        # Initialization
        self.initialize(self.t)

        # Main loop
        for k in range(N+1):
            self.step()
            self._log(variables_to_log)


        for block in self.model.blocks.values():
            try:
                block.finalize()
            except Exception as e:
                print(f"[WARNING] finalize() failed for block {block.name}: {e}")


        return self.logs
