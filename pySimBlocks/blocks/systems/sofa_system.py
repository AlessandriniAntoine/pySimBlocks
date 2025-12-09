from multiprocessing import Process, Pipe
import numpy as np
import importlib.util
from pySimBlocks.core.block import Block


def sofa_worker(conn, scene_file, input_keys, output_keys):
    import os
    import sys
    import Sofa
    import importlib.util
    import numpy as np

    scene_dir = os.path.dirname(os.path.abspath(scene_file))
    if scene_dir not in sys.path:
        sys.path.insert(0, scene_dir)

    # 1. Import scene
    spec = importlib.util.spec_from_file_location("scene", scene_file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    root = Sofa.Core.Node("root")
    root, controller = mod.createScene(root)
    Sofa.Simulation.initRoot(root)

    dt = float(root.dt.value)

    # First animate
    Sofa.Simulation.animate(root, dt)

    # Send initial outputs
    initial = {k: np.asarray(controller.outputs[k]).reshape(-1,1) for k in output_keys}
    conn.send(initial)

    # 2. Main loop
    while True:
        msg = conn.recv()

        if msg["cmd"] == "step":
            # apply inputs
            for key, val in msg["inputs"].items():
                controller.inputs[key] = val

            Sofa.Simulation.animate(root, dt)

            outputs = {k: np.asarray(controller.outputs[k]).reshape(-1,1)
                       for k in output_keys}
            conn.send(outputs)

        elif msg["cmd"] == "stop":
            break

    conn.close()


class SofaSystem(Block):
    """
    SOFA system block.

    Description:
        Computes:
            out(t) = SOFA_simulation_step(in(t))

    Parameters:
        name: str
            Block name.
        scene_file: str
            Path to the SOFA scene file (Python script).
        input_keys: list of str
            List of input keys for the SOFA controller.
        output_keys: list of str
            List of output keys for the SOFA controller.

    Inputs:
        Dynamic — specified by input_keys.

    Outputs:
        Dynamic — specified by output_keys.
    """

    direct_feedthrough = False

    def __init__(self,
        name: str,
        scene_file: str,
        input_keys: list[str],
        output_keys: list[str]
    ):
        super().__init__(name)

        self.scene_file = scene_file
        self.input_keys = input_keys
        self.output_keys = output_keys

        for k in input_keys:
            self.inputs[k] = None
        for k in output_keys:
            self.outputs[k] = None

        self.process = None
        self.conn = None

        self.state["internal"] = 0
        self.next_state["interna"] = 0


    def initialize(self, t0: float):

        # Start worker
        parent_conn, child_conn = Pipe()
        self.conn = parent_conn

        self.process = Process(
            target=sofa_worker,
            args=(child_conn, self.scene_file,
                  self.input_keys, self.output_keys)
        )
        self.process.start()

        # Receive initial outputs
        initial_outputs = self.conn.recv()

        for k in self.output_keys:
            self.outputs[k] = initial_outputs[k]


    def output_update(self, t: float):
        """
        Outputs were already updated during the previous state_update().
        This block retrieves outputs from an external SOFA worker process,
        so no computation is required here.
        """
        pass


    def state_update(self, t: float, dt: float):

        # Send inputs
        msg = {"cmd": "step", "inputs": {}}
        for k in self.input_keys:
            val = self.inputs[k]
            if val is None:
                raise RuntimeError(
                    f"[{self.name}] Input '{k}' is missing at time {t}."
                )
            msg["inputs"][k] = val

        self.conn.send(msg)

        # Receive outputs
        outputs = self.conn.recv()

        for k in self.output_keys:
            self.outputs[k] = outputs[k]

        self.next_state["internal"] = self.state["internal"] + 1


    def finalize(self):
        """Ensure worker process is shutdown cleanly."""
        if self.conn:
            try:
                self.conn.send({"cmd": "stop"})
            except:
                pass
            try:
                self.conn.close()
            except:
                pass

        if self.process:
            self.process.join(timeout=1.0)
            if self.process.is_alive():
                self.process.kill()


    def __del__(self):
        if self.conn:
            try:
                self.conn.send({"cmd": "stop"})
            except:
                pass
        if self.process:
            self.process.join(timeout=0.5)
