from multiprocessing import Process, Pipe
import numpy as np
from typing import Dict, List
from pySimBlocks.core.block import Block


def sofa_worker(conn, scene_file, input_keys, output_keys):
    import os
    import sys
    import Sofa
    import importlib.util

    scene_dir = os.path.dirname(os.path.abspath(scene_file))
    if scene_dir not in sys.path:
        sys.path.insert(0, scene_dir)

    # 1. Import scene
    spec = importlib.util.spec_from_file_location("scene", scene_file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    root = Sofa.Core.Node("root")
    root, controller = mod.createScene(root)
    controller.SOFA_MASTER = False
    Sofa.Simulation.initRoot(root)

    dt = float(root.dt.value)

    while not controller.IS_READY:
        controller.prepare_scene()
        if controller.IS_READY:
            break
        Sofa.Simulation.animate(root, dt)

    # Send initial outputs
    controller.get_outputs()
    initial = {k: np.asarray(controller.outputs[k]).reshape(-1,1) for k in output_keys}
    conn.send(initial)

    # 2. Main loop
    while True:
        msg = conn.recv()

        if msg["cmd"] == "step":
            # apply inputs
            for key, val in msg["inputs"].items():
                controller.inputs[key] = val

            controller.set_inputs()
            Sofa.Simulation.animate(root, dt)
            controller.get_outputs()

            outputs = {k: np.asarray(controller.outputs[k]).reshape(-1,1)
                       for k in output_keys}
            conn.send(outputs)

        elif msg["cmd"] == "stop":
            break

    conn.close()


class SofaPlant(Block):
    """
    SOFA-based dynamic plant block.

    Summary:
        Executes a SOFA simulation as a dynamic system driven by pySimBlocks.
        At each control step, inputs are sent to SOFA, the scene advances,
        and updated outputs are returned.

    Parameters (overview):
        scene_file : str
            Path to the SOFA scene file.
        input_keys : list[str]
            Names of input signals exchanged with SOFA.
        output_keys : list[str]
            Names of output signals produced by SOFA.
        sample_time : float, optional
            Block execution period.

    I/O:
        Inputs:
            Defined dynamically by input_keys.
        Outputs:
            Defined dynamically by output_keys.

    Notes:
        - This block runs SOFA in a separate worker process.
        - The block has internal state and no direct feedthrough.
    """

    direct_feedthrough = False
    need_first = True

    def __init__(self,
        name: str,
        scene_file: str,
        input_keys: list[str],
        output_keys: list[str],
        slider_params: Dict[str, List[float]] | None = None,
        sample_time: float | None = None
    ):
        super().__init__(name, sample_time)

        self.scene_file = scene_file
        self.input_keys = input_keys
        self.output_keys = output_keys
        self.slider_params = slider_params

        for k in input_keys:
            self.inputs[k] = None
            self.next_outputs = {}
        for k in output_keys:
            self.outputs[k] = None
            self.state[k] = None
            self.next_state[k] = None

        self.process = None
        self.conn = None



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
            self.state[k] = initial_outputs[k]
            self.next_state[k] = initial_outputs[k]


    def output_update(self, t: float, dt: float):
        """
        Outputs were already updated during the previous state_update().
        This block retrieves outputs from an external SOFA worker process,
        so no computation is required here.
        """
        for key in self.output_keys:
            self.outputs[key] = self.state[key]


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
            self.next_state[k] = outputs[k]


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
